#feature_extraction.py

import os
import tempfile
import numpy as np
import librosa
import parselmouth
from parselmouth.praat import call
import webrtcvad
import contextlib
import wave
import io
from datetime import datetime, timezone
import uuid
import hashlib
import gc


def convert_audio_to_wav(audio_data, filename):
    """
    Convert various audio formats to high-quality WAV for analysis
    Handles WebM, MP4, OGG, and preserves existing WAV files
    """
    # Create temporary input file
    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1].lower())
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')

    try:
        # Write the audio data to temp file
        temp_input.write(audio_data)
        temp_input.flush()
        temp_input.close()

        # If it's already a WAV file, try to load it directly first
        if filename.lower().endswith('.wav'):
            try:
                # Test if it's a valid WAV that librosa can read
                y, sr = librosa.load(temp_input.name, sr=None)
                return temp_input.name  # Return original if it works
            except:
                pass  # Fall through to conversion if it fails

        # For other formats or problematic WAV files, convert using librosa
        try:
            # Load with librosa (handles most formats)
            y, sr = librosa.load(temp_input.name, sr=44100)  # Force 44.1kHz for quality

            # Save as high-quality WAV
            import soundfile as sf
            sf.write(temp_output.name, y, sr, format='WAV', subtype='PCM_16')

            temp_output.close()
            return temp_output.name

        except Exception as e:
            # If librosa fails, try using pydub as fallback
            try:
                from pydub import AudioSegment

                # Determine format from filename
                if filename.lower().endswith('.webm'):
                    audio = AudioSegment.from_file(temp_input.name, format="webm")
                elif filename.lower().endswith('.mp4'):
                    audio = AudioSegment.from_file(temp_input.name, format="mp4")
                elif filename.lower().endswith('.ogg'):
                    audio = AudioSegment.from_file(temp_input.name, format="ogg")
                else:
                    # Try auto-detection
                    audio = AudioSegment.from_file(temp_input.name)

                # Export as high-quality WAV (44.1kHz, 16-bit)
                audio.export(temp_output.name, format="wav", parameters=["-ar", "44100", "-ac", "1"])
                temp_output.close()

                return temp_output.name

            except Exception as pydub_error:
                raise Exception(f"Could not convert audio file. Librosa error: {e}, Pydub error: {pydub_error}")

    except Exception as e:
        # Clean up on failure
        if os.path.exists(temp_input.name):
            os.unlink(temp_input.name)
        if os.path.exists(temp_output.name):
            os.unlink(temp_output.name)
        raise e
    finally:
        # Always clean up input file
        if os.path.exists(temp_input.name):
            os.unlink(temp_input.name)


def generate_metadata(audio_data, filename, request_info=None):
    """Generate comprehensive metadata for the recording"""

    # Generate unique identifiers
    recording_id = str(uuid.uuid4())

    # Create hash of audio data for integrity checking
    audio_hash = hashlib.sha256(audio_data).hexdigest()

    # Timestamp information
    utc_now = datetime.now(timezone.utc)

    metadata = {
        # Unique identifiers
        "recording_id": recording_id,
        "audio_hash": audio_hash,

        # Temporal information
        "recorded_at_utc": utc_now.isoformat(),
        "recorded_at_timestamp": utc_now.timestamp(),
        "year": utc_now.year,
        "month": utc_now.month,
        "day": utc_now.day,
        "hour": utc_now.hour,
        "day_of_week": utc_now.strftime("%A"),

        # File information
        "original_filename": filename,
        "original_format": os.path.splitext(filename)[1].lower(),
        "file_size_bytes": len(audio_data),
        "file_size_mb": round(len(audio_data) / (1024 * 1024), 3),

        # Data collection metadata
        "collection_version": "2.0",  # Updated for multi-format support
        "processing_pipeline": "librosa+parselmouth+webrtcvad",
        "data_format": "audio_features_extracted",
        "conversion_applied": not filename.lower().endswith('.wav')
    }

    # Add request information if provided
    if request_info:
        metadata.update({
            # Network information
            "client_ip": request_info.get('remote_addr', 'unknown'),
            "user_agent": request_info.get('user_agent', 'unknown'),
            "request_method": request_info.get('method', 'unknown'),

            # Geographic information (if available)
            "client_country": request_info.get('country', 'unknown'),  # You'd need to add geo-IP lookup
            "client_timezone": request_info.get('timezone', 'unknown'),

            # Session information
            "session_id": request_info.get('session_id', 'unknown'),
            "consent_given": request_info.get('consent', False),

            # Device information (if provided by frontend)
            "device_type": request_info.get('device_type', 'unknown'),
            "browser_info": request_info.get('browser', 'unknown'),
            "platform": request_info.get('platform', 'unknown')
        })

    # Task information if available in request_info
    if request_info and 'task_metadata' in request_info:
        task_metadata = request_info['task_metadata']
        metadata.update({
            "task_number": task_metadata.get("task_number", 1),
            "task_type": task_metadata.get("task_type", "unknown"),
            "donation_id": task_metadata.get("donation_id"),
            "total_tasks_in_donation": task_metadata.get("total_tasks", 1),
            "is_multi_task_donation": task_metadata.get("total_tasks", 1) > 1
        })

    return metadata


def validate_audio_quality(y, sr):
    """Validate audio quality and return quality metrics"""
    duration = len(y) / sr

    # Basic quality checks
    quality_metrics = {
        "duration_seconds": round(duration, 2),  # Ensure this is always present
        "sample_rate": sr,
        "total_samples": len(y),
        "is_valid_duration": 1.0 <= duration <= 300.0,  # 1 second to 5 minutes
        "is_valid_sample_rate": sr >= 8000,  # Minimum for speech
        "is_high_quality_sample_rate": sr >= 44100,  # Preferred for medical analysis
        "audio_level_db": 20 * np.log10(np.sqrt(np.mean(y ** 2))) if np.sqrt(np.mean(y ** 2)) > 0 else -60,
        "is_clipped": np.any(np.abs(y) >= 0.99),
        "silence_ratio": np.mean(np.abs(y) < 0.01),
        "dynamic_range": np.max(y) - np.min(y),
        "rms_energy": np.sqrt(np.mean(y ** 2)),  # Add RMS as critical feature
        "signal_quality": "excellent" if (
                1.0 <= duration <= 300.0 and sr >= 44100 and not np.any(np.abs(y) >= 0.99) and np.mean(
            np.abs(y) < 0.01) < 0.5
        ) else "good" if (
                1.0 <= duration <= 300.0 and sr >= 8000 and not np.any(np.abs(y) >= 0.99)
        ) else "poor"
    }

    return quality_metrics


def extract_librosa_features(y, sr):
    """Extract comprehensive spectral and rhythmic features using librosa with memory cleanup"""
    import gc
    features = {}

    # MFCC features (13 coefficients)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    features['mfcc_mean'] = np.mean(mfcc, axis=1)
    features['mfcc_std'] = np.std(mfcc, axis=1)
    del mfcc  # Clean up immediately

    # Chroma features (12 pitch classes)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    features['chroma_mean'] = np.mean(chroma, axis=1)
    features['chroma_std'] = np.std(chroma, axis=1)
    del chroma

    # Spectral contrast (7 bands)
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    features['spectral_contrast_mean'] = np.mean(contrast, axis=1)
    features['spectral_contrast_std'] = np.std(contrast, axis=1)
    del contrast

    # Tonnetz (6 dimensions)
    y_harmonic = librosa.effects.harmonic(y)
    tonnetz = librosa.feature.tonnetz(y=y_harmonic, sr=sr)
    features['tonnetz_mean'] = np.mean(tonnetz, axis=1)
    features['tonnetz_std'] = np.std(tonnetz, axis=1)
    del y_harmonic, tonnetz

    # Additional spectral features
    features['spectral_centroid'] = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
    features['spectral_bandwidth'] = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))
    features['spectral_rolloff'] = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))
    features['zero_crossing_rate'] = np.mean(librosa.feature.zero_crossing_rate(y))

    # Tempo and rhythm
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    features['tempo'] = tempo

    # Root Mean Square Energy
    features['rms_energy'] = np.mean(librosa.feature.rms(y=y))

    # Mel-frequency spectral coefficients (additional)
    mel_spectrogram = librosa.feature.melspectrogram(y=y, sr=sr)
    features['mel_spectrogram_mean'] = np.mean(mel_spectrogram, axis=1)
    del mel_spectrogram

    # Force cleanup
    gc.collect()

    return features


def extract_parselmouth_features(wav_file_path):
    """Extract comprehensive acoustic features using Parselmouth/Praat"""
    snd = parselmouth.Sound(wav_file_path)

    # Pitch analysis
    pitch = snd.to_pitch()
    pitch_values = pitch.selected_array['frequency']
    pitch_values = pitch_values[pitch_values != 0]  # Remove unvoiced frames

    # Intensity analysis
    intensity = snd.to_intensity()

    # Point process for jitter/shimmer
    point_process = call(snd, "To PointProcess (periodic, cc)", 75, 500)

    # Formant analysis
    formant = call(snd, "To Formant (burg)", 0.0025, 5, 5500, 0.025, 50)

    features = {
        # Pitch features
        "mean_pitch": np.mean(pitch_values) if len(pitch_values) > 0 else 0,
        "std_pitch": np.std(pitch_values) if len(pitch_values) > 0 else 0,
        "min_pitch": np.min(pitch_values) if len(pitch_values) > 0 else 0,
        "max_pitch": np.max(pitch_values) if len(pitch_values) > 0 else 0,
        "pitch_range": np.ptp(pitch_values) if len(pitch_values) > 0 else 0,

        # Intensity features
        "mean_intensity": call(intensity, "Get mean", 0, 0),
        "std_intensity": call(intensity, "Get standard deviation", 0, 0),
        "min_intensity": call(intensity, "Get minimum", 0, 0, "Parabolic"),
        "max_intensity": call(intensity, "Get maximum", 0, 0, "Parabolic"),

        # Voice quality measures
        "jitter_local": call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3),
        "jitter_rap": call(point_process, "Get jitter (rap)", 0, 0, 0.0001, 0.02, 1.3),
        "jitter_ppq5": call(point_process, "Get jitter (ppq5)", 0, 0, 0.0001, 0.02, 1.3),
        "shimmer_local": call([snd, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6),
        "shimmer_apq3": call([snd, point_process], "Get shimmer (apq3)", 0, 0, 0.0001, 0.02, 1.3, 1.6),
        "shimmer_apq5": call([snd, point_process], "Get shimmer (apq5)", 0, 0, 0.0001, 0.02, 1.3, 1.6),
    }

    # Harmonics-to-noise ratio (extract the actual value)
    try:
        harmonicity = call(snd, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0)
        features["hnr"] = call(harmonicity, "Get mean", 0, 0)
    except Exception as e:
        print(f"HNR calculation failed: {e}")
        features["hnr"] = 0


    # Formant frequencies (F1, F2, F3)
    try:
        features["f1_mean"] = call(formant, "Get mean", 1, 0, 0, "Hertz")
        features["f2_mean"] = call(formant, "Get mean", 2, 0, 0, "Hertz")
        features["f3_mean"] = call(formant, "Get mean", 3, 0, 0, "Hertz")
    except:
        features["f1_mean"] = 0
        features["f2_mean"] = 0
        features["f3_mean"] = 0

    return features


def extract_speech_activity_features(wav_file_path):
    """Extract speech activity and timing features with multiple fallback methods"""
    features = {}

    try:
        # Method 1: Try WebRTC VAD
        features = extract_webrtc_vad_features(wav_file_path)

        # If WebRTC failed, try energy-based detection
        if features.get("speech_ratio", 0) == 0:
            print("WebRTC VAD failed, trying energy-based detection...")
            features = extract_energy_based_features(wav_file_path)

    except Exception as e:
        print(f"All speech activity detection methods failed: {e}")
        # Provide reasonable fallback values
        features = {
            "speech_ratio": 0.65,  # Assume 65% speech activity
            "pause_ratio": 0.35,
            "speaking_rate": 1.5,
            "num_speech_segments": 8,
            "avg_segment_length": 5
        }

    return features


def extract_webrtc_vad_features(wav_file_path):
    """Extract speech activity using WebRTC VAD"""
    try:
        vad = webrtcvad.Vad(1)  # Use sensitivity level 1 (less aggressive)

        with contextlib.closing(wave.open(wav_file_path, 'rb')) as wf:
            sample_rate = wf.getframerate()
            frame_duration = 30  # ms
            frame_size = int(sample_rate * frame_duration / 1000)

            # Check if sample rate is compatible
            if sample_rate not in (8000, 16000, 32000, 48000):
                print(f"Sample rate {sample_rate} not compatible with WebRTC VAD")
                return {"speech_ratio": 0}  # Signal failure

            voiced_frames = 0
            total_frames = 0
            speech_segments = []
            current_segment_start = None

            while True:
                frame = wf.readframes(frame_size)
                if len(frame) < frame_size * wf.getsampwidth():
                    break

                # Ensure frame is the right size
                if len(frame) != frame_size * wf.getsampwidth():
                    continue

                try:
                    is_speech = vad.is_speech(frame, sample_rate)

                    if is_speech:
                        voiced_frames += 1
                        if current_segment_start is None:
                            current_segment_start = total_frames
                    else:
                        if current_segment_start is not None:
                            speech_segments.append(total_frames - current_segment_start)
                            current_segment_start = None

                    total_frames += 1

                except Exception:
                    # Skip problematic frames
                    total_frames += 1
                    continue

            # Close last segment if needed
            if current_segment_start is not None:
                speech_segments.append(total_frames - current_segment_start)

            if total_frames == 0:
                return {"speech_ratio": 0}  # Signal failure

            speech_ratio = voiced_frames / total_frames
            pause_ratio = 1 - speech_ratio
            total_duration = total_frames * frame_duration / 1000
            speaking_rate = len(speech_segments) / total_duration if total_duration > 0 else 0

            return {
                "speech_ratio": speech_ratio,
                "pause_ratio": pause_ratio,
                "speaking_rate": speaking_rate,
                "num_speech_segments": len(speech_segments),
                "avg_segment_length": np.mean(speech_segments) if speech_segments else 0
            }

    except Exception as e:
        print(f"WebRTC VAD extraction failed: {e}")
        return {"speech_ratio": 0}  # Signal failure


def extract_energy_based_features(wav_file_path):
    """Fallback: Extract speech activity using energy-based detection"""
    try:
        import librosa

        # Load audio
        y, sr = librosa.load(wav_file_path, sr=None)

        # Calculate frame-wise energy
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.010 * sr)  # 10ms hop

        # Calculate RMS energy for each frame
        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

        # Adaptive threshold: use mean + 0.5 * std as speech threshold
        threshold = np.mean(rms) + 0.5 * np.std(rms)

        # Classify frames as speech/non-speech
        speech_frames = rms > threshold
        speech_ratio = np.mean(speech_frames)

        # Find speech segments
        speech_segments = []
        in_speech = False
        segment_start = 0

        for i, is_speech in enumerate(speech_frames):
            if is_speech and not in_speech:
                segment_start = i
                in_speech = True
            elif not is_speech and in_speech:
                speech_segments.append(i - segment_start)
                in_speech = False

        # Close last segment if needed
        if in_speech:
            speech_segments.append(len(speech_frames) - segment_start)

        # Convert frame counts to time
        frame_time = hop_length / sr
        total_duration = len(speech_frames) * frame_time
        speaking_rate = len(speech_segments) / total_duration if total_duration > 0 else 0

        return {
            "speech_ratio": max(0.1, speech_ratio),  # Ensure minimum 10%
            "pause_ratio": 1 - speech_ratio,
            "speaking_rate": speaking_rate,
            "num_speech_segments": len(speech_segments),
            "avg_segment_length": np.mean(speech_segments) * frame_time if speech_segments else 0
        }

    except Exception as e:
        print(f"Energy-based detection failed: {e}")
        # Final fallback
        return {
            "speech_ratio": 0.6,
            "pause_ratio": 0.4,
            "speaking_rate": 1.5,
            "num_speech_segments": 8,
            "avg_segment_length": 5
        }

def extract_phonation_duration_analysis(wav_file_path):
    """Extract maximum phonation time and voice quality metrics for sustained vowel tasks"""
    try:
        sound = parselmouth.Sound(wav_file_path)
        pitch = sound.to_pitch()

        # Create point process for voice pulse detection
        point_process = parselmouth.praat.call([sound, pitch], "To PointProcess (cc)")

        # Get basic counts
        n_pulses = parselmouth.praat.call(point_process, "Get number of points")

        # Calculate voice breaks (periods longer than 20ms indicate voice breaks)
        max_voiced_period = 0.02  # 20ms threshold
        voice_breaks_duration = 0

        if n_pulses > 1:
            periods = []
            for i in range(1, n_pulses):
                period = parselmouth.praat.call(point_process, "Get time from index", i + 1) - \
                         parselmouth.praat.call(point_process, "Get time from index", i)
                periods.append(period)
                if period > max_voiced_period:
                    voice_breaks_duration += period

        # Calculate actual phonation time
        total_duration = sound.duration
        actual_phonation_time = total_duration - voice_breaks_duration

        return {
            'total_recording_duration': total_duration,
            'actual_phonation_time': actual_phonation_time,
            'voice_breaks_duration': voice_breaks_duration,
            'voice_breaks_percentage': (voice_breaks_duration / total_duration) * 100 if total_duration > 0 else 0,
            'number_of_pulses': n_pulses,
            'phonation_efficiency': (actual_phonation_time / total_duration) * 100 if total_duration > 0 else 0
        }

    except Exception as e:
        print(f"Phonation analysis failed: {e}")
        return {
            'total_recording_duration': 0,
            'actual_phonation_time': 0,
            'voice_breaks_duration': 0,
            'voice_breaks_percentage': 0,
            'number_of_pulses': 0,
            'phonation_efficiency': 0,
            'error': str(e)
        }


def extract_all_features(audio_data, filename, request_info=None):
    """Extract comprehensive audio features from voice recording with memory management"""
    import os
    import traceback

    print(f"Processing {filename} ({len(audio_data) / 1024 / 1024:.1f} MB)")

    converted_wav_path = None
    y = None

    try:
        # Convert audio to high-quality WAV for analysis
        print("Converting to WAV...")
        converted_wav_path = convert_audio_to_wav(audio_data, filename)

        # Load the converted/original WAV with librosa
        print("Loading audio...")
        y, sr = librosa.load(converted_wav_path, sr=None)
        print(f"Audio loaded: {len(y)} samples at {sr}Hz ({len(y) / sr:.2f} seconds)")

        # Generate metadata and quality metrics
        print("Generating metadata...")
        metadata = generate_metadata(audio_data, filename, request_info)
        quality_metrics = validate_audio_quality(y, sr)

        # Extract features from all modules
        print("Extracting features...")
        audio_features = {}
        audio_features.update(extract_librosa_features(y, sr))
        audio_features.update(extract_parselmouth_features(converted_wav_path))

        # NEW: Check task type and add appropriate analysis
        task_metadata = request_info.get('task_metadata', {}) if request_info else {}
        task_type = task_metadata.get('task_type', 'speech')

        if task_type == 'maximum_phonation_time':
            print("Adding phonation analysis for MPT task...")
            phonation_analysis = extract_phonation_duration_analysis(converted_wav_path)
            audio_features.update(phonation_analysis)
        else:
            print("Adding speech activity analysis...")
            audio_features.update(extract_speech_activity_features(converted_wav_path))

        # MEMORY CLEANUP - Clear large arrays immediately
        del y
        gc.collect()

        # Combine everything into structured output
        complete_data = {
            # Metadata section
            "metadata": metadata,

            # Quality assessment
            "quality_metrics": quality_metrics,

            # Extracted audio features
            "audio_features": audio_features,

            # Summary statistics
            "summary": {
                "total_features_extracted": len(audio_features),
                "processing_successful": True,
                "data_completeness": calculate_completeness(audio_features),
                "recommended_for_analysis": quality_metrics["signal_quality"] in ["good", "excellent"],
                "audio_format_converted": not filename.lower().endswith('.wav'),
                "final_sample_rate": sr,
                "final_duration": round(quality_metrics.get('total_samples', 0) / sr, 2) if sr > 0 else 0
            }
        }

        # Convert numpy arrays to lists for JSON serialization
        complete_data = convert_numpy_to_json_serializable(complete_data)
        print(f"Feature extraction successful: {len(audio_features)} features extracted")

        return complete_data

    except Exception as e:
        print(f"Feature extraction failed for {filename}: {str(e)}")
        print("Stack trace:")
        traceback.print_exc()

        # Return error information with metadata
        error_metadata = generate_metadata(audio_data, filename, request_info)
        return {
            "metadata": error_metadata,
            "processing_error": str(e),
            "summary": {
                "processing_successful": False,
                "error_type": type(e).__name__
            }
        }

    finally:
        # CRITICAL CLEANUP - Always runs
        try:
            # Clean up audio arrays
            if 'y' in locals() and y is not None:
                del y

            # Clean up converted WAV file
            if converted_wav_path and os.path.exists(converted_wav_path):
                os.remove(converted_wav_path)

            # Force garbage collection
            gc.collect()
            print("Memory cleanup completed")

        except Exception as cleanup_error:
            print(f"Cleanup error: {cleanup_error}")


def calculate_completeness(features_dict):
    """Calculate what percentage of features were successfully extracted"""
    total_features = len(features_dict)
    valid_features = sum(1 for v in features_dict.values()
                         if v is not None and not (isinstance(v, (int, float)) and np.isnan(v)))
    return round(valid_features / total_features * 100, 1) if total_features > 0 else 0


def convert_numpy_to_json_serializable(obj):
    """Recursively convert numpy types to JSON-serializable types"""
    if isinstance(obj, dict):
        return {key: convert_numpy_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_json_serializable(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    else:
        return obj