# validate_voice_data_v3.py - Updated for Multi-Task Donation System

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
import json

warnings.filterwarnings('ignore')
load_dotenv()


class VoiceDataValidatorV3:
    def __init__(self):
        """Initialize validator for multi-task donation system"""
        self.dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        self.table = self.dynamodb.Table('voice-donations')

        # Task-specific validation ranges
        self.mpt_ranges = {
            "actual_phonation_time": (1, 45),  # 1-45 seconds for MPT
            "phonation_efficiency": (50, 100),  # 50-100% efficiency
            "voice_breaks_percentage": (0, 30),  # 0-30% voice breaks
        }

        self.speech_ranges = {
            "mean_pitch": (80, 400),
            "speech_ratio": (0.3, 0.9),
            "quality_duration_seconds": (25, 65),  # 25-65s for speech tasks
            "hnr": (5, 25),
        }

    def convert_decimal_to_float(self, obj):
        """Convert DynamoDB Decimal types to float"""
        if isinstance(obj, dict):
            return {key: self.convert_decimal_to_float(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_decimal_to_float(item) for item in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj

    def fetch_all_data(self):
        """Fetch voice donation records from June 26th onwards, excluding test recordings"""
        print("📥 Fetching data from DynamoDB (June 26th onwards)...")

        response = self.table.scan()
        items = response['Items']

        while 'LastEvaluatedKey' in response:
            response = self.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])

        # Filter for June 26th onwards (2024-06-26)
        cutoff_date = datetime(2024, 6, 26)
        filtered_items = []
        test_recordings = 0

        for item in items:
            created_at = item.get('created_at', '')

            # Check if it's a test recording
            is_test = False
            questionnaire = item.get('questionnaire', {})
            responses = questionnaire.get('responses', {})
            condition_specs = responses.get('condition_specifications', {})

            # Check for "test SC" in any specification field, especially otherGeneralCondition
            for field_name, spec_value in condition_specs.items():
                if isinstance(spec_value, str) and 'test sc' in spec_value.lower():
                    is_test = True
                    test_recordings += 1
                    break

            # Also check health_conditions array for other_general + the text field
            health_conditions = responses.get('health_conditions', [])
            if ('other_general' in health_conditions and
                    condition_specs.get('otherGeneralCondition', '').lower().strip() in ['test sc', 'test']):
                is_test = True
                test_recordings += 1

            if is_test:
                continue  # Skip test recordings

            if created_at:
                try:
                    # Parse ISO datetime string
                    item_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if item_date.replace(tzinfo=None) >= cutoff_date:
                        filtered_items.append(item)
                except ValueError:
                    # If date parsing fails, include the item to be safe
                    filtered_items.append(item)

        print(f"✅ Found {len(filtered_items)} real voice donation records since June 26th")
        print(f"   (Filtered out {len(items) - len(filtered_items) - test_recordings} older records)")
        print(f"   (Excluded {test_recordings} test recordings with 'test SC')")
        return filtered_items

    def analyze_donation_completeness(self, items):
        """Analyze donation completion rates and multi-task success"""
        print("\n🎯 DONATION COMPLETENESS ANALYSIS")
        print("=" * 50)

        # Group by donation_id
        donations = {}
        for item in items:
            item = self.convert_decimal_to_float(item)
            donation_id = item.get('donation_id', item['recording_id'])

            if donation_id not in donations:
                donations[donation_id] = {
                    'recordings': [],
                    'expected_tasks': 1,
                    'completed_tasks': 0,
                    'failed_tasks': 0,
                    'status': 'unknown'
                }

            donations[donation_id]['recordings'].append(item)

            # Get expected task count - check multiple fields
            task_metadata = item.get('task_metadata', {})
            if task_metadata:
                # Try different field names for total tasks
                expected = (task_metadata.get('total_tasks_in_donation') or
                            task_metadata.get('total_tasks') or
                            3)  # Default to 3 for multi-task system
                donations[donation_id]['expected_tasks'] = expected

            # Count completed/failed
            if item.get('status') == 'completed':
                donations[donation_id]['completed_tasks'] += 1
            elif item.get('status') == 'failed':
                donations[donation_id]['failed_tasks'] += 1

        # Analyze donation success rates
        total_donations = len(donations)
        completed_donations = 0
        partial_donations = 0
        failed_donations = 0
        multi_task_donations = 0

        for donation_id, donation in donations.items():
            expected = donation['expected_tasks']
            completed = donation['completed_tasks']
            failed = donation['failed_tasks']

            if expected > 1:
                multi_task_donations += 1

            if completed == expected and failed == 0:
                completed_donations += 1
                donation['status'] = 'completed'
            elif completed > 0:
                partial_donations += 1
                donation['status'] = 'partial'
            else:
                failed_donations += 1
                donation['status'] = 'failed'

        print(f"Total Donations: {total_donations}")
        print(f"Multi-task Donations: {multi_task_donations} ({multi_task_donations / total_donations * 100:.1f}%)")
        print(f"Fully Completed Donations: {completed_donations} ({completed_donations / total_donations * 100:.1f}%)")
        print(f"Partial Donations: {partial_donations} ({partial_donations / total_donations * 100:.1f}%)")
        print(f"Failed Donations: {failed_donations} ({failed_donations / total_donations * 100:.1f}%)")

        # Show completed donations breakdown
        if completed_donations > 0:
            print(f"\n✅ COMPLETED DONATIONS BREAKDOWN:")
            print(f"   Total completed recordings: {completed_donations * 3}")
            print(f"   This represents {completed_donations} people who finished all 3 tasks")

        return donations

    def analyze_task_distribution(self, items):
        """Analyze distribution of different task types (completed donations only)"""
        print("\n📊 TASK TYPE DISTRIBUTION (COMPLETED ONLY)")
        print("=" * 50)

        # Only count completed recordings
        completed_items = [item for item in items if item.get('status') == 'completed']

        task_counts = {
            'maximum_phonation_time': 0,
            'picture_description': 0,
            'weekend_question': 0,
            'unknown': 0
        }

        # Count completed recordings by task type
        for item in completed_items:
            task_metadata = item.get('task_metadata', {})
            task_type = task_metadata.get('task_type', 'unknown')
            task_counts[task_type] = task_counts.get(task_type, 0) + 1

        total_completed = sum(task_counts.values())

        print(f"Total Completed Recordings: {total_completed}")
        print(f"Completed Donations (assuming 3 tasks each): {total_completed // 3}")
        print("")

        for task_type, count in task_counts.items():
            percentage = (count / total_completed * 100) if total_completed > 0 else 0
            donations_count = count  # Each recording represents one task completion
            print(f"{task_type}: {count} completed recordings ({percentage:.1f}%)")

        # Additional insight: Check for incomplete donation sets
        if total_completed % 3 != 0:
            incomplete_recordings = total_completed % 3
            print(f"\n⚠️  Note: {incomplete_recordings} recordings suggest incomplete donation sets")

        return task_counts

    def validate_task_specific_features(self, items):
        """Validate features based on task type"""
        print("\n🔍 TASK-SPECIFIC FEATURE VALIDATION")
        print("=" * 50)

        issues = []

        for item in items:
            item = self.convert_decimal_to_float(item)
            recording_id = item['recording_id']
            task_metadata = item.get('task_metadata', {})
            task_type = task_metadata.get('task_type', 'unknown')

            if 'audio_features' not in item:
                continue

            features = item['audio_features'].get('audio_features', {})

            if task_type == 'maximum_phonation_time':
                # Validate MPT-specific features
                for feature, (min_val, max_val) in self.mpt_ranges.items():
                    if feature in features:
                        value = features[feature]
                        # Safe numeric conversion
                        try:
                            value = float(value)
                            if not (min_val <= value <= max_val):
                                issues.append(
                                    f"MPT {recording_id}: {feature} = {value:.2f} (expected: {min_val}-{max_val})")
                        except (ValueError, TypeError):
                            issues.append(f"MPT {recording_id}: {feature} = '{value}' (invalid numeric value)")

            elif task_type in ['picture_description', 'weekend_question']:
                # Validate speech task features
                for feature, (min_val, max_val) in self.speech_ranges.items():
                    if feature in features:
                        value = features[feature]
                        # Safe numeric conversion
                        try:
                            value = float(value)
                            if not (min_val <= value <= max_val):
                                issues.append(
                                    f"Speech {recording_id}: {feature} = {value:.2f} (expected: {min_val}-{max_val})")
                        except (ValueError, TypeError):
                            issues.append(f"Speech {recording_id}: {feature} = '{value}' (invalid numeric value)")

        print(f"Found {len(issues)} task-specific validation issues")
        for issue in issues[:10]:  # Show first 10
            print(f"  ⚠️  {issue}")

        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more issues")

        return issues

    def analyze_questionnaire_v3(self, items):
        """Analyze new enhanced questionnaire data"""
        print("\n📋 ENHANCED QUESTIONNAIRE ANALYSIS")
        print("=" * 50)

        # Only analyze unique donations (not individual recordings)
        seen_donations = set()
        donation_data = []

        for item in items:
            donation_id = item.get('donation_id', item['recording_id'])
            if donation_id in seen_donations:
                continue
            seen_donations.add(donation_id)

            questionnaire = item.get('questionnaire', {})
            responses = questionnaire.get('responses', {})
            flags = questionnaire.get('analysis_flags', {})

            donation_data.append({
                'donation_id': donation_id,
                'responses': responses,
                'flags': flags
            })

        df = pd.DataFrame(donation_data)
        total_donations = len(df)

        print(f"Unique Donations Analyzed: {total_donations}")

        # Language distribution
        print(f"\n🌍 LANGUAGE DISTRIBUTION:")
        languages = df.apply(lambda x: x['responses'].get('donation_language', 'unknown'), axis=1)
        english_count = (languages == 'english').sum()
        arabic_count = (languages == 'arabic').sum()
        unknown_count = (languages == 'unknown').sum()

        print(f"  English: {english_count} donations ({english_count / total_donations * 100:.1f}%)")
        print(f"  Arabic: {arabic_count} donations ({arabic_count / total_donations * 100:.1f}%)")
        if unknown_count > 0:
            print(f"  Unknown: {unknown_count} donations ({unknown_count / total_donations * 100:.1f}%)")

        # Health condition analysis
        print(f"\n🏥 HEALTH CONDITION DISTRIBUTION:")
        has_condition_count = 0
        healthy_count = 0
        unknown_health_count = 0

        for _, row in df.iterrows():
            flags = row['flags']
            responses = row['responses']

            # Check if person has any health condition
            has_any_condition = flags.get('has_any_condition', None)

            if has_any_condition is True:
                has_condition_count += 1
            elif has_any_condition is False:
                healthy_count += 1
            else:
                # Fallback: check health_conditions in responses
                health_conditions = responses.get('health_conditions', [])
                if isinstance(health_conditions, list):
                    if 'none' in health_conditions:
                        healthy_count += 1
                    elif len(health_conditions) > 0:
                        has_condition_count += 1
                    else:
                        unknown_health_count += 1
                else:
                    unknown_health_count += 1

        print(
            f"  Has Health Condition(s): {has_condition_count} donations ({has_condition_count / total_donations * 100:.1f}%)")
        print(f"  Healthy (No Conditions): {healthy_count} donations ({healthy_count / total_donations * 100:.1f}%)")
        if unknown_health_count > 0:
            print(
                f"  Unknown Health Status: {unknown_health_count} donations ({unknown_health_count / total_donations * 100:.1f}%)")

        # Age distribution
        print(f"\n👥 AGE DISTRIBUTION:")
        ages = df.apply(lambda x: x['responses'].get('age_group', 'unknown'), axis=1)
        for age, count in ages.value_counts().items():
            print(f"  {age}: {count} donations ({count / total_donations * 100:.1f}%)")

        # Detailed health condition breakdown (if people have conditions)
        if has_condition_count > 0:
            print(f"\n🔍 DETAILED CONDITION BREAKDOWN:")
            condition_flags = [
                ('has_neurological_condition', 'Neurological'),
                ('has_respiratory_condition', 'Respiratory'),
                ('has_mood_condition', 'Mood/Psychiatric'),
                ('has_voice_condition', 'Voice Problems'),
                ('has_metabolic_condition', 'Metabolic/Endocrine')
            ]

            for flag, label in condition_flags:
                count = df.apply(lambda x: x['flags'].get(flag, False), axis=1).sum()
                if count > 0:
                    print(f"  {label}: {count} donations ({count / total_donations * 100:.1f}%)")

        # Cross-analysis: Language vs Health
        print(f"\n🔄 LANGUAGE vs HEALTH CROSS-ANALYSIS:")
        english_healthy = 0
        english_condition = 0
        arabic_healthy = 0
        arabic_condition = 0

        for _, row in df.iterrows():
            language = row['responses'].get('donation_language', 'unknown')
            has_condition = row['flags'].get('has_any_condition', None)

            if has_condition is None:
                # Fallback check
                health_conditions = row['responses'].get('health_conditions', [])
                if isinstance(health_conditions, list) and 'none' in health_conditions:
                    has_condition = False
                elif isinstance(health_conditions, list) and len(health_conditions) > 0:
                    has_condition = True

            if language == 'english':
                if has_condition:
                    english_condition += 1
                else:
                    english_healthy += 1
            elif language == 'arabic':
                if has_condition:
                    arabic_condition += 1
                else:
                    arabic_healthy += 1

        print(f"  English - Healthy: {english_healthy}, With Conditions: {english_condition}")
        print(f"  Arabic - Healthy: {arabic_healthy}, With Conditions: {arabic_condition}")

        return df

    def generate_dashboard_data(self, items, donations):
        """Generate key metrics for dashboard"""
        print("\n📈 GENERATING DASHBOARD METRICS")
        print("=" * 50)

        # Convert to DataFrames for analysis
        items_df = pd.DataFrame([self.convert_decimal_to_float(item) for item in items])

        # Basic counts
        total_recordings = len(items)
        total_donations = len(donations)
        completed_recordings = len(items_df[items_df['status'] == 'completed'])

        # Success rates
        donation_success_rate = sum(1 for d in donations.values() if d['status'] == 'completed') / total_donations * 100
        recording_success_rate = completed_recordings / total_recordings * 100

        # Quality metrics (for completed recordings only)
        completed_items = items_df[items_df['status'] == 'completed']

        avg_features_extracted = 0
        avg_duration = 0
        excellent_quality_count = 0

        if len(completed_items) > 0:
            # Extract feature counts
            feature_counts = []
            durations = []
            quality_ratings = []

            for _, item in completed_items.iterrows():
                if 'audio_features' in item and pd.notna(item['audio_features']):
                    audio_features = item['audio_features']
                    if isinstance(audio_features, dict):
                        features = audio_features.get('audio_features', {})
                        summary = audio_features.get('summary', {})
                        quality = audio_features.get('quality_metrics', {})

                        if features:
                            feature_counts.append(len(features))
                        if 'final_duration' in summary:
                            durations.append(summary['final_duration'])
                        if quality.get('signal_quality') == 'excellent':
                            excellent_quality_count += 1

            if feature_counts:
                avg_features_extracted = np.mean(feature_counts)
            if durations:
                avg_duration = np.mean(durations)

        # Task distribution
        task_counts = self.analyze_task_distribution(items)

        dashboard_data = {
            'overview': {
                'total_recordings': total_recordings,
                'total_donations': total_donations,
                'completed_recordings': completed_recordings,
                'donation_success_rate': round(donation_success_rate, 1),
                'recording_success_rate': round(recording_success_rate, 1),
            },
            'quality': {
                'avg_features_extracted': round(avg_features_extracted, 1),
                'avg_duration_seconds': round(avg_duration, 1),
                'excellent_quality_count': excellent_quality_count,
                'excellent_quality_rate': round(excellent_quality_count / completed_recordings * 100,
                                                1) if completed_recordings > 0 else 0
            },
            'tasks': task_counts,
            'system_health_score': None,  # Will be set by the main validation function
            'timestamp': datetime.now().isoformat()
        }

        # Save dashboard data
        with open('dashboard_data.json', 'w') as f:
            json.dump(dashboard_data, f, indent=2)

        print("Dashboard data saved to 'dashboard_data.json'")
        print("\nKey Metrics:")
        print(f"  Total Donations: {total_donations}")
        print(f"  Donation Success Rate: {donation_success_rate:.1f}%")
        print(f"  Average Features per Recording: {avg_features_extracted:.1f}")
        print(f"  Excellent Quality Rate: {dashboard_data['quality']['excellent_quality_rate']:.1f}%")

        return dashboard_data

    def run_full_validation(self):
        """Run complete validation for multi-task system"""
        print("🔬 VOICE DATA VALIDATION V3.0 - MULTI-TASK SYSTEM")
        print("=" * 60)

        # Fetch and analyze data
        items = self.fetch_all_data()
        if not items:
            print("❌ No data found")
            return None

        # Multi-task specific analyses
        donations = self.analyze_donation_completeness(items)
        task_distribution = self.analyze_task_distribution(items)
        task_validation_issues = self.validate_task_specific_features(items)
        questionnaire_analysis = self.analyze_questionnaire_v3(items)

        # Generate dashboard data
        dashboard_data = self.generate_dashboard_data(items, donations)

        # Overall health assessment
        total_issues = len(task_validation_issues)
        donation_success_rate = dashboard_data['overview']['donation_success_rate']

        health_score = max(0, 100 - total_issues - (100 - donation_success_rate))

        # Add health score to dashboard data
        dashboard_data['system_health_score'] = round(health_score, 1)

        print(f"\n🎯 OVERALL SYSTEM HEALTH SCORE: {health_score:.1f}/100")

        if health_score >= 90:
            print("✅ EXCELLENT: Multi-task donation system is working perfectly!")
        elif health_score >= 70:
            print("✅ GOOD: Minor issues detected, system is functional")
        elif health_score >= 50:
            print("⚠️  FAIR: Some issues detected, review recommended")
        else:
            print("🚨 NEEDS ATTENTION: Multiple issues detected")

        return {
            'items': items,
            'donations': donations,
            'dashboard_data': dashboard_data,
            'health_score': health_score
        }


def main():
    """Run the updated validation"""
    validator = VoiceDataValidatorV3()
    results = validator.run_full_validation()
    return results


if __name__ == "__main__":
    results = main()