import shutil
from nltk import edit_distance
import numpy as np
import os
from pathlib import Path
import pandas as pd
from pathlib import Path
from pydub import AudioSegment
import re
from sklearn.model_selection import train_test_split


def process_raw_audio_clips(data_dir = '/home/mepstein/voice_to_text/data', adjust_freq=None):
    ''' takes all audio files from 'RAW_AUDIO_DIR', processes them 
        and adds new files to FINAL_AUDIO_DIR and TRANSCRIPT_DIR
        
    cons:
        - relies on manual process to only ever add an audio file once to raw-audio-dir,
          otherwise duplicates would end up in output dirs
        - if/when some new change to audio-preprocessing steps becomes necessary, this 
          can't re-generate everything from raw-data-archive/
        '''
    
    # Constants
    RAW_AUDIO_DIR = Path(f"{data_dir}/audio_raw")
    FINAL_AUDIO_DIR = Path(f"{data_dir}/audio_wav4")
    TRANSCRIPTS_DIR = Path(f"{data_dir}/transcripts")
    AUDIO_RAW_ARCHIVE = Path(f"{data_dir}/audio_raw_archive")
    
    # files in audio_wav4/ and transcripts/ are named a{i}.wav & t{i}.txt. 
    file_nums = [int(f.name.split('.')[0][1:]) for f in Path(FINAL_AUDIO_DIR).glob('*')]
    num_final_audio_files = max(file_nums)
    num_new_audio_files = len(list(RAW_AUDIO_DIR.glob('*')))
    
    i = int(num_final_audio_files) + 1
    for f in Path(RAW_AUDIO_DIR).glob('*'):
        # write raw-audio filename as transcript txt file
        filename_and_transcript = f.name.split('.')[0]

        # standardize punctuation - if final character is not a period, add a period
        if filename_and_transcript[-1] not in ('.', '?'):
            filename_and_transcript = filename_and_transcript + '.'
            
        with open(f"{TRANSCRIPTS_DIR}/t{i}.txt", "w") as txtfile:
            txtfile.write(filename_and_transcript)
        
        # convert raw-audio from m4a to wav4 and save to new directory
        voice_clip = AudioSegment.from_file(f, format="m4a")
        if adjust_freq is not None:
            assert 1_000 < adjust_freq < 60_000, "are you sure your `adjust_freq` param units are correct?"
            voice_clip = voice_clip.set_frame_rate(adjust_freq)
        
        voice_clip.export(out_f = f'{FINAL_AUDIO_DIR}/a{i}.wav4', format='wav')
        
        # I need to clear audio_raw dir so new copies of same audio aren't moved over to audio_wav next
        # time this is run. But don't want to just delete them in case I ever need to recreate 
        # audio_wav from scratch
        shutil.move(f, f"{AUDIO_RAW_ARCHIVE}/{f.name}")
        
        # increment counter for filenames in audio-wav/ and transcripts/ folders
        i = i+1
        
    return None


def process_raw_audio_clips2(data_dir = '/home/mepstein/voice_to_text/data', 
                             regenerate_all = False,
                             adjust_freq=None):
    ''' Process audio files from raw_data_archive/ and populate final_audio_dir and transcripts
    params
    -------
    data_dir: directory of data files (raw and final)
    regenerate_all: if True, wipe final_audio_dir and transcripts and process all files in 
                    raw_audio_dir. If False, only process files not already found 
                    in transcripts/
    adjust_freq: If None, don't adjust khz of audio files. 
                 If not None, must be integer. Adjust khz of audio files to value
    '''
    # Constants
    RAW_AUDIO_DIR = Path(f"{data_dir}/audio_raw")
    FINAL_AUDIO_DIR = Path(f"{data_dir}/audio_wav4")
    TRANSCRIPTS_DIR = Path(f"{data_dir}/transcripts")
    RAW_AUDIO_ARCHIVE = Path(f"{data_dir}/audio_raw_archive")
    
    # optionally wipe final audio/transcripts dir and process all files in raw-audio-archive
    if regenerate_all:
        files_to_process = list(RAW_AUDIO_ARCHIVE.glob('*'))
        for folder in [FINAL_AUDIO_DIR, TRANSCRIPTS_DIR]:
            shutil.rmtree(folder)
            os.mkdir(folder)
    
    # otherwise identify just the new files, to process those 
    else:
        candidate_files = list(Path(RAW_AUDIO_ARCHIVE).glob('*'))
        already_processed = [open(tf, 'r').read().replace('\n', '') for tf in TRANSCRIPTS_DIR.glob('*')]
        
        files_to_process = []
        for f in candidate_files:
            EPSILON_EDIT_DISTANCE = 3
            min_edit_distance = 999
            for ap in already_processed:
                f_trans = f.name.split('.')[0]
                if edit_distance(f_trans, ap) <= min_edit_distance:
                    min_edit_distance = edit_distance(f_trans, ap)
            if min_edit_distance > EPSILON_EDIT_DISTANCE:
                files_to_process.append(f)
        print("found new audio files to process...")
        print(files_to_process)
    
    # files in audio_wav4/ and transcripts/ are named a{i}.wav & t{i}.txt. 
    # (i) will start at 1 if FINAL_AUDIO_DIR is empty (e.g. if regenerate_all==True)
    file_nums = [int(f.name.split('.')[0][1:]) for f in Path(FINAL_AUDIO_DIR).glob('*')]
    i = max(file_nums + [0]) + 1
    
    for f in files_to_process:
        print(f'processing {f}')
        filename_and_transcript = f.name.split('.')[0]
        
        if filename_and_transcript[-1] not in ('.', '?'):
            filename_and_transcript = filename_and_transcript + '.'
        
        ## write transcript file
        with open(f"{TRANSCRIPTS_DIR}/t{i}.txt", "w") as txtfile:
            txtfile.write(filename_and_transcript)
        
        ## save processed audio file 
        voice_clip = AudioSegment.from_file(f, format="m4a")
        if adjust_freq is not None:
            assert 1_000 < adjust_freq < 60_000, "are you sure your `adjust_freq` param units are correct?"
            voice_clip = voice_clip.set_frame_rate(adjust_freq)
        
        voice_clip.export(out_f = f'{FINAL_AUDIO_DIR}/a{i}.wav4', format='wav')
        
        # increment counter for filenames in audio-wav/ and transcripts/ folders
        i = i+1
        
    return None

process_raw_audio_clips2()

def generate_deepspeech_CSVs(data_dir = '/home/mepstein/voice_to_text/data',
                             ds_csv_dir='/home/mepstein/voice_to_text/data/ds_csvs',
                             train_val_test_splits=(.60, .20, .20)):
    ''' Generate CSVs that DeepSpeech requires with info on audio/transcript data
    
    params
    ------
    data_dir: the directory where audio(wav4) and transcript(.txt) files live
    ds_csv_dir: the diretory where this function will deposit train.csv, val.csv and test.csv
    train_val_test_splits: the percentage of audio clips to allocate to train/val/test sets
    '''
    
    # Input Validation
    assert sum(train_val_test_splits) == 1.0
    
    # Constants
    AUDIO_DIR = Path(f"{data_dir}/audio_wav4")
    TRANSCRIPTS_DIR = Path(f"{data_dir}/transcripts")
    
    # Create DataFrame for CSV fields that DeepSpeech needs:
    audio_files = list(AUDIO_DIR.glob('*'))
    file_sizes = [os.path.getsize(x) for x in audio_files]
    transcript_filenames = [f"t{x.name[1:].split('.')[0]}.txt" for x in audio_files]
    transcript_files = [Path(f"{TRANSCRIPTS_DIR}/{tn}") for tn in transcript_filenames]
    transcripts = [re.sub('[?_’!:;,.\n]', '', open(tf, 'r').read().lower()).replace('-',' ') for tf in transcript_files]
    df = pd.DataFrame({'wav_filename': audio_files,
                       'wav_filesize': file_sizes,
                       'transcript':   transcripts})
    # Divide DataFrame into train/val/test components, output as CSVs
    train_pct = train_val_test_splits[0]
    val_pct   = train_val_test_splits[1]
    test_pct  = train_val_test_splits[2]
    
    train, test = train_test_split(df, test_size=test_pct)
    train, val  = train_test_split(train, test_size=(val_pct / (val_pct + train_pct)))
    
    train.to_csv(f'{ds_csv_dir}/train.csv', index=False)
    val.to_csv(f'{ds_csv_dir}/val.csv', index=False)
    test.to_csv(f'{ds_csv_dir}/test.csv', index=False)
    
    return None