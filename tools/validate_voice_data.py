# validate_voice_data.py

import boto3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from decimal import Decimal
import os
from dotenv import load_dotenv
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()


class VoiceDataValidator:
    def __init__(self):
        """Initialize the validator with DynamoDB connection"""
        self.dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        self.table = self.dynamodb.Table('voice-donations')

        # Realistic ranges based on actual voice data analysis
        self.expected_ranges = {
            # Pitch features (Hz) - based on real speech data
            "mean_pitch": (80, 400),  # Wide range for all voice types
            "min_pitch": (50, 300),  # Lower bound for deep voices
            "max_pitch": (150, 800),  # Upper bound for high pitches/peaks
            "std_pitch": (10, 200),  # Pitch variation range
            "pitch_range": (100, 700),  # Total pitch span

            # Voice quality (realistic clinical ranges)
            "jitter_local": (0, 0.08),  # Up to 8% jitter (clinical threshold)
            "jitter_rap": (0, 0.08),
            "jitter_ppq5": (0, 0.08),
            "shimmer_local": (0, 0.4),  # Up to 40% shimmer (realistic for normal speech)
            "shimmer_apq3": (0, 0.4),
            "shimmer_apq5": (0, 0.4),

            # Intensity (dB) - microphone and environment dependent
            "mean_intensity": (30, 80),  # Realistic recording levels
            "max_intensity": (40, 90),
            "min_intensity": (20, 70),
            "std_intensity": (1, 15),

            # Harmonics-to-noise ratio (dB) - forgiving for home recordings
            "hnr": (3, 25),  # 3dB+ is acceptable for non-studio recordings

            # Speech activity - realistic for description tasks
            "speech_ratio": (0.2, 0.9),  # 20-90% (description tasks have pauses)
            "pause_ratio": (0.1, 0.8),  # Complementary to speech ratio
            "speaking_rate": (0.5, 8),  # Wide range of speaking speeds
            "num_speech_segments": (5, 200),  # Varies greatly by task

            # Duration (seconds)
            "quality_duration_seconds": (25, 45),  # Your target range

            # Formants (Hz) - accommodate all demographics
            "f1_mean": (200, 1000),  # First formant realistic range
            "f2_mean": (800, 3500),  # Second formant realistic range
            "f3_mean": (1500, 4500),  # Third formant realistic range

            # Energy features - device dependent
            "quality_rms_energy": (0.001, 0.1),  # Realistic energy levels
            "rms_energy": (0.001, 0.1),  # Duplicate check

            # Spectral features - based on speech analysis literature
            "spectral_centroid": (400, 3000),  # Spectral center frequency
            "spectral_bandwidth": (1000, 4000),  # Spectral spread
            "spectral_rolloff": (800, 4000),  # High frequency rolloff
            "zero_crossing_rate": (0.005, 0.1),  # Zero crossing frequency
            "tempo": (60, 200),  # Speech tempo range
        }

        # Critical features that should never be zero/missing
        self.critical_features = [
            "mean_pitch", "mean_intensity", "quality_duration_seconds",
            "speech_ratio", "quality_rms_energy"
        ]

    def convert_decimal_to_float(self, obj):
        """Convert DynamoDB Decimal types to float for analysis"""
        if isinstance(obj, dict):
            return {key: self.convert_decimal_to_float(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_decimal_to_float(item) for item in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj

    def fetch_all_data(self):
        """Fetch all voice donation records from DynamoDB"""
        print("📥 Fetching data from DynamoDB...")

        response = self.table.scan()
        items = response['Items']

        # Handle pagination if there are many records
        while 'LastEvaluatedKey' in response:
            response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])

        print(f"✅ Found {len(items)} voice donation records")
        return items

    def extract_features_dataframe(self, items):
        """Extract audio features into a pandas DataFrame for analysis"""
        print("🔄 Processing audio features...")

        records = []
        for item in items:
            # Convert Decimals to floats
            item = self.convert_decimal_to_float(item)

            # Extract basic info
            record = {
                'recording_id': item['recording_id'],
                'created_at': item['created_at']
            }

            # Extract audio features
            if 'audio_features' in item and 'audio_features' in item['audio_features']:
                features = item['audio_features']['audio_features']
                record.update(features)

            # Extract quality metrics
            if 'audio_features' in item and 'quality_metrics' in item['audio_features']:
                quality = item['audio_features']['quality_metrics']
                for key, value in quality.items():
                    record[f"quality_{key}"] = value

            # Extract questionnaire data - UPDATED FOR NEW SCHEMA
            if 'questionnaire' in item and 'responses' in item['questionnaire']:
                responses = item['questionnaire']['responses']
                for key, value in responses.items():
                    # Handle arrays (like chronic_conditions) properly
                    if isinstance(value, list):
                        record[f"survey_{key}"] = ', '.join(value)  # Convert to string for analysis
                        # Also create individual boolean columns for conditions
                        if key == 'chronic_conditions':
                            for condition in ['respiratory', 'neurological', 'cardiovascular', 'other', 'none']:
                                record[f"survey_has_{condition}"] = condition in value
                    else:
                        record[f"survey_{key}"] = value

            # Extract analysis flags - NEW IN SCHEMA v2.1
            if 'questionnaire' in item and 'analysis_flags' in item['questionnaire']:
                flags = item['questionnaire']['analysis_flags']
                for key, value in flags.items():
                    record[f"flag_{key}"] = value

            records.append(record)

        df = pd.DataFrame(records)
        print(f"✅ Processed {len(df)} records with {len(df.columns)} features")
        return df

    def validate_feature_ranges(self, df):
        """Check if features fall within expected healthy ranges"""
        print("\n🔍 FEATURE RANGE VALIDATION")
        print("=" * 50)

        issues = []

        for feature, (min_val, max_val) in self.expected_ranges.items():
            if feature in df.columns:
                values = df[feature].dropna()
                if len(values) == 0:
                    continue

                outliers = values[(values < min_val) | (values > max_val)]
                outlier_percentage = len(outliers) / len(values) * 100

                print(f"{feature:25s}: {values.min():.4f} - {values.max():.4f} "
                      f"(expected: {min_val:.4f} - {max_val:.4f}) "
                      f"| {outlier_percentage:.1f}% outliers")

                # Show actual values for debugging
                if len(values) <= 5:  # If few samples, show all values
                    actual_values = ", ".join([f"{v:.4f}" for v in values])
                    print(f"{'':27s}  Actual values: [{actual_values}]")

                if outlier_percentage > 50:  # Only flag if >50% are outliers (more lenient)
                    issues.append(f"⚠️  {feature}: {outlier_percentage:.1f}% of values outside normal range")

        return issues

    def check_critical_features(self, df):
        """Check for missing or zero critical features"""
        print("\n🚨 CRITICAL FEATURE CHECK")
        print("=" * 50)

        issues = []

        for feature in self.critical_features:
            if feature in df.columns:
                values = df[feature].dropna()
                zero_count = len(values[values == 0])
                missing_count = len(df) - len(values)

                print(f"{feature:20s}: {missing_count} missing, {zero_count} zero values")

                if zero_count > 0:
                    issues.append(f"🚨 {feature}: {zero_count} records have zero values")
                if missing_count > 0:
                    issues.append(f"🚨 {feature}: {missing_count} records missing this feature")
            else:
                issues.append(f"🚨 {feature}: Feature completely missing from data")

        return issues

    def analyze_data_quality(self, df):
        """Analyze overall data quality metrics"""
        print("\n📊 DATA QUALITY ANALYSIS")
        print("=" * 50)

        total_records = len(df)
        print(f"Total Records: {total_records}")

        # Check duration distribution
        if 'quality_duration_seconds' in df.columns:
            durations = df['quality_duration_seconds'].dropna()
            print(f"Duration Range: {durations.min():.1f}s - {durations.max():.1f}s")
            print(f"Average Duration: {durations.mean():.1f}s")

            target_duration = durations[(durations >= 25) & (durations <= 45)]
            print(f"Within Target Duration (25-45s): {len(target_duration)}/{len(durations)} "
                  f"({len(target_duration) / len(durations) * 100:.1f}%)")

        # Check signal quality
        if 'quality_signal_quality' in df.columns:
            quality_counts = df['quality_signal_quality'].value_counts()
            print(f"\nSignal Quality Distribution:")
            for quality, count in quality_counts.items():
                print(f"  {quality}: {count} ({count / total_records * 100:.1f}%)")

        # Check language distribution - NEW
        if 'survey_donation_language' in df.columns:
            language_counts = df['survey_donation_language'].value_counts()
            print(f"\nDonation Language Distribution:")
            for language, count in language_counts.items():
                print(f"  {language}: {count} ({count / total_records * 100:.1f}%)")

        # Check for demographic distribution
        if 'survey_age_group' in df.columns:
            age_counts = df['survey_age_group'].value_counts()
            print(f"\nAge Group Distribution:")
            for age, count in age_counts.items():
                print(f"  {age}: {count} ({count / total_records * 100:.1f}%)")

        # Check chronic conditions distribution - NEW
        if 'survey_chronic_conditions' in df.columns:
            print(f"\nChronic Conditions Distribution:")
            # Count each condition separately since it's now an array
            for condition in ['none', 'respiratory', 'neurological', 'cardiovascular', 'other']:
                col_name = f'survey_has_{condition}'
                if col_name in df.columns:
                    count = df[col_name].sum()
                    print(f"  {condition}: {count} ({count / total_records * 100:.1f}%)")

        # Analysis flags summary - NEW
        flag_columns = [col for col in df.columns if col.startswith('flag_')]
        if flag_columns:
            print(f"\nAnalysis Flags Summary:")
            for flag_col in flag_columns:
                if df[flag_col].dtype == 'bool':
                    true_count = df[flag_col].sum()
                    print(f"  {flag_col.replace('flag_', '')}: {true_count} ({true_count / total_records * 100:.1f}%)")
                elif df[flag_col].dtype in ['object', 'str']:
                    value_counts = df[flag_col].value_counts()
                    print(f"  {flag_col.replace('flag_', '')}:")
                    for value, count in value_counts.items():
                        print(f"    {value}: {count} ({count / total_records * 100:.1f}%)")

    def check_questionnaire_data_quality(self, df, total_records=None):
        """NEW: Check questionnaire data quality specifically"""
        print("\n📋 QUESTIONNAIRE DATA QUALITY")
        print("=" * 50)

        total_records = len(df)

        # Check for required fields completion
        required_fields = [
            'survey_donation_language',
            'survey_age_group',
            'survey_chronic_conditions',
            'survey_voice_problems',
            'survey_native_language',  # NEW
            'survey_arabic_dialect'  # NEW
        ]

        for field in required_fields:
            if field in df.columns:
                missing_count = df[field].isna().sum()
                completion_rate = ((len(df) - missing_count) / len(df)) * 100
                print(f"{field.replace('survey_', ''):20s}: {completion_rate:.1f}% completion rate")
            else:
                print(f"{field.replace('survey_', ''):20s}: MISSING from data")

        # Check conditional field logic
        if 'survey_has_other' in df.columns and 'survey_other_condition' in df.columns:
            other_selected = df['survey_has_other'].sum()
            other_specified = df['survey_other_condition'].notna().sum()
            print(f"\nConditional Field Check:")
            print(f"  'Other' condition selected: {other_selected}")
            print(f"  'Other' condition specified: {other_specified}")
            if other_selected != other_specified:
                print(f"  ⚠️  Mismatch: {abs(other_selected - other_specified)} records missing conditional data")

        # Check voice problems conditional logic
        if 'survey_voice_problems' in df.columns and 'survey_other_voice_problem' in df.columns:
            other_voice_selected = (df['survey_voice_problems'] == 'other').sum()
            other_voice_specified = df['survey_other_voice_problem'].notna().sum()
            print(f"  'Other' voice problem selected: {other_voice_selected}")
            print(f"  'Other' voice problem specified: {other_voice_specified}")
            if other_voice_selected != other_voice_specified:
                print(
                    f"  ⚠️  Mismatch: {abs(other_voice_selected - other_voice_specified)} voice problem records missing conditional data")

        # Language distribution analysis
        if 'survey_native_language' in df.columns:
            native_lang_counts = df['survey_native_language'].value_counts()
            print(f"\nNative Language Distribution:")
            for lang, count in native_lang_counts.items():
                print(f"  {lang}: {count} ({count / total_records * 100:.1f}%)")

        if 'survey_arabic_dialect' in df.columns:
            dialect_counts = df['survey_arabic_dialect'].value_counts()
            print(f"\nArabic Dialect Distribution:")
            for dialect, count in dialect_counts.items():
                print(f"  {dialect}: {count} ({count / total_records * 100:.1f}%)")

        # Cross-language validation
        if 'survey_donation_language' in df.columns:
            print(f"\nLanguage Consistency Check:")
            english_donations = (df['survey_donation_language'] == 'english').sum()
            arabic_donations = (df['survey_donation_language'] == 'arabic').sum()

            if 'survey_native_language' in df.columns:
                native_lang_provided = df['survey_native_language'].notna().sum()
                print(f"  English donations with native language data: {native_lang_provided}/{english_donations}")

            if 'survey_arabic_dialect' in df.columns:
                dialect_provided = df['survey_arabic_dialect'].notna().sum()
                print(f"  Arabic donations with dialect data: {dialect_provided}/{arabic_donations}")

    def suggest_optimal_ranges(self, df):
        """Suggest optimal ranges based on actual data distribution"""
        print("\n🎯 SUGGESTED OPTIMAL RANGES (Based on Your Data)")
        print("=" * 60)

        suggested_ranges = {}

        for feature in df.columns:
            if feature.startswith(
                    ('mean_', 'std_', 'min_', 'max_', 'jitter_', 'shimmer_', 'hnr', 'speech_', 'pause_', 'f1_', 'f2_',
                     'f3_', 'quality_')):
                values = df[feature].dropna()
                if len(values) == 0:
                    continue

                # Skip boolean and non-numeric columns
                if values.dtype == 'bool' or values.dtype == 'object':
                    continue

                # Skip if all values are the same (no range to calculate)
                if len(values.unique()) <= 1:
                    continue

                try:
                    # Calculate percentile-based ranges (5th to 95th percentile)
                    min_val = np.percentile(values, 5)
                    max_val = np.percentile(values, 95)

                    # Add some padding (±20% for robustness)
                    padding = (max_val - min_val) * 0.2
                    suggested_min = max(0, min_val - padding) if min_val >= 0 else min_val - padding
                    suggested_max = max_val + padding

                    suggested_ranges[feature] = (suggested_min, suggested_max)

                    print(f"{feature:25s}: {suggested_min:.4f} - {suggested_max:.4f} "
                          f"(current data: {values.min():.4f} - {values.max():.4f})")

                except (TypeError, ValueError) as e:
                    # Skip features that can't be processed
                    print(f"{feature:25s}: Skipped (data type: {values.dtype})")
                    continue

        return suggested_ranges

    def create_feature_plots(self, df):
        """Create visualization plots for key features"""
        print("\n📈 Creating feature distribution plots...")

        # Select key features for plotting
        plot_features = [
            'mean_pitch', 'jitter_local', 'shimmer_local', 'hnr',
            'speech_ratio', 'quality_duration_seconds'
        ]

        available_features = [f for f in plot_features if f in df.columns]

        if len(available_features) == 0:
            print("❌ No key features available for plotting")
            return

        # Create subplots
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('Voice Feature Distributions', fontsize=16)

        for i, feature in enumerate(available_features[:6]):
            row, col = i // 3, i % 3
            ax = axes[row, col]

            values = df[feature].dropna()

            # Histogram
            ax.hist(values, bins=20, alpha=0.7, edgecolor='black')
            ax.set_title(f'{feature}\n(n={len(values)})')
            ax.set_xlabel('Value')
            ax.set_ylabel('Frequency')

            # Add expected range if available
            if feature in self.expected_ranges:
                min_val, max_val = self.expected_ranges[feature]
                ax.axvline(min_val, color='red', linestyle='--', alpha=0.7, label='Expected Min')
                ax.axvline(max_val, color='red', linestyle='--', alpha=0.7, label='Expected Max')
                ax.legend()

        # Hide empty subplots
        for i in range(len(available_features), 6):
            row, col = i // 3, i % 3
            axes[row, col].set_visible(False)

        plt.tight_layout()
        plt.savefig('voice_feature_distributions.png', dpi=300, bbox_inches='tight')
        print("✅ Saved plot as 'voice_feature_distributions.png'")
        plt.show()

    def generate_summary_report(self, df, range_issues, critical_issues):
        """Generate a comprehensive validation summary"""
        print("\n" + "=" * 60)
        print("🎯 VOICE DATA VALIDATION SUMMARY REPORT")
        print("=" * 60)

        total_records = len(df)

        # Overall health score (more lenient scoring)
        total_issues = len(range_issues) + len(critical_issues)
        health_score = max(0, 100 - (total_issues * 5))  # Reduced penalty per issue

        print(f"📊 OVERALL DATA HEALTH SCORE: {health_score}/100")

        if health_score >= 90:
            print("✅ EXCELLENT: Your voice data extraction is working perfectly!")
        elif health_score >= 70:
            print("✅ GOOD: Minor issues detected, but overall quality is very acceptable")
        elif health_score >= 50:
            print("⚠️  FAIR: Some issues detected, but pipeline is functional")
        elif health_score >= 30:
            print("🔶 NEEDS ATTENTION: Several issues detected, review recommended")
        else:
            print("🚨 POOR: Significant issues detected, pipeline needs attention")

        print(f"\n📈 Data Summary:")
        print(f"  • Total voice donations: {total_records}")
        print(f"  • Range validation issues: {len(range_issues)}")
        print(f"  • Critical feature issues: {len(critical_issues)}")

        # NEW: Language distribution summary
        if 'survey_donation_language' in df.columns:
            lang_counts = df['survey_donation_language'].value_counts()
            print(f"  • Languages: {dict(lang_counts)}")

        if range_issues:
            print(f"\n⚠️  Range Issues:")
            for issue in range_issues:
                print(f"    {issue}")

        if critical_issues:
            print(f"\n🚨 Critical Issues:")
            for issue in critical_issues:
                print(f"    {issue}")

        if not range_issues and not critical_issues:
            print("\n🎉 No major issues detected! Your voice extraction pipeline appears to be working correctly.")

        print(f"\n💡 Recommendations:")
        if len(range_issues) > 5:
            print("  • The current validation ranges may be too restrictive for your data")
            print("  • Consider using the suggested optimal ranges shown above")
            print("  • This is normal for initial testing - ranges can be adjusted")

        if health_score < 80:
            print("  • Review audio quality of problematic recordings")
            print("  • Check microphone settings and recording environment")
            print("  • Verify feature extraction algorithms")

        print("  • Continue testing with diverse voice samples")
        print("  • Consider demographic balance in your test data")
        print("  • Test both English and Arabic recordings for language-specific patterns")
        print("  • Monitor data quality as you scale up")

    def run_full_validation(self):
        """Run complete validation pipeline"""
        print("🔬 VOICE DATA VALIDATION STARTING...")
        print("=" * 60)

        # Fetch data
        items = self.fetch_all_data()
        if not items:
            print("❌ No data found in DynamoDB table")
            return

        # Process into DataFrame
        df = self.extract_features_dataframe(items)

        # Run validations
        range_issues = self.validate_feature_ranges(df)
        critical_issues = self.check_critical_features(df)

        # Quality analysis
        self.analyze_data_quality(df)

        # NEW: Questionnaire quality check
        self.check_questionnaire_data_quality(df)

        # Suggest optimal ranges
        suggested_ranges = self.suggest_optimal_ranges(df)

        # Create plots
        self.create_feature_plots(df)

        # Generate summary
        self.generate_summary_report(df, range_issues, critical_issues)

        return df


def main():
    """Main function to run validation"""
    validator = VoiceDataValidator()
    df = validator.run_full_validation()
    return df


if __name__ == "__main__":
    # Required packages: pip install pandas matplotlib seaborn boto3
    df = main()