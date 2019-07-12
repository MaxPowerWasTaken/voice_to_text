import os
import subprocess
from src.data_processing import process_raw_audio_clips2, generate_deepspeech_CSVs

def train():

    # TF seems to need this, see: https://github.com/mozilla/DeepSpeech/issues/2211
    os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'

    # data prep
    process_raw_audio_clips2(data_dir  = '/home/mepstein/voice_to_text/data')
    generate_deepspeech_CSVs(data_dir = '/home/mepstein/voice_to_text/data',
                                ds_csv_dir='/home/mepstein/voice_to_text/data/ds_csvs',
                                train_val_test_splits=(.75, .15, .10))
    
    # (re)Train DeepSpeech's pretrained English model on our voice audio/transcript data
    # using early-stopping to save checkpoint model once performance on validation set starts
    # to degrade
    
    # how to pass 'params' to deepspeech programmatically in python? everything seems to come from FLAG (global var) attributes
    # e.g. train() function in top-level DeepSpeech.py takes no params. All 'params' come from 
    # FLAG attributes initialized by combination of defaults in util/config and CLI params...
    # Seems to me that I'd have to either...
    #   1) from python call DeepSpeech using CLI (via e.g. subprocess)
    #   2) or make changes to DeepSpeech repo itself.
    
    # (backup plan would be to call via subprocess/cli as here: https://github.com/mozilla/DeepSpeech/issues/2185)
    # As far as I can tell the most accurate/comprehensive list of commands available 
    # is at: https://github.com/mozilla/DeepSpeech/blob/master/util/flags.py (or rather, that file on my local filesystem in vendor/DeepSpeech...)


    # run deepspeech
    DS = "vendor/DeepSpeech"
    RETRAINED_MODELS_FOLDER="models_retrained_3"
    DEEPSPEECH_CMD_NO_TRANSFER = f"""
    python3 {DS}/DeepSpeech.py \
            --train_files data/ds_csvs/train.csv \
            --dev_files data/ds_csvs/val.csv \
            --test_files data/ds_csvs/test.csv \
            --checkpoint_dir {RETRAINED_MODELS_FOLDER} \
            --epochs 101 \
            --train_batch_size 4 \
            --dev_batch_size 4 \
            --test_batch_size 4 \
            --es_steps 10 \
            --checkpoint_step 1 \
            --learning_rate 0.00001 \
            --dropout_rate 0.15 \
            --lm_alpha 0.75 \
            --lm_beta 1.85 \
            --export_dir {RETRAINED_MODELS_FOLDER} \
            --alphabet_config_path {DS}/models-0.5.1/alphabet.txt \
            --lm_binary_path {DS}/models-0.5.1/lm.binary \
            --lm_trie_path {DS}/models-0.5.1/trie \
            --beam_width 1024
    """
    #subprocess.call(DEEPSPEECH_CMD, shell=True)
    # HOLD UP - where's the pbmm actual model file? I'm not actually using the pretrained model file here...???
    
    
    # ... new command (run from vendor/DeepSpeech bc that's how I got it to work first...)
    """
    (voice_to_text) mepstein@pop-os:~/voice_to_text/vendor/DeepSpeech$ 
    python DeepSpeech.py \
        --n_hidden 2048 \
        --checkpoint_dir ../../deepspeech-0.5.1-checkpoint/ \
        --epochs 50 \
        --train_files ../../data/ds_csvs/train.csv \
        --dev_files ../../data/ds_csvs/val.csv \
        --test_files ../../data/ds_csvs/test.csv \
        --learning_rate 0.0001 \
        --train_batch_size 4 \
        --dev_batch_size 4 \
        --test_batch_size 4 \
        --es_steps 15 \
        --lm_binary_path models-0.5.1/lm.binary \
        --lm_trie_path models-0.5.1/trie \
        --export_dir ../../models_retrained_1
    """ 
    # NOTE: might want to do that from a freshly downloaded release .5.1 release checkpoint, to ensure that 
    #       and ensure that when I run an experimental transfer-learning run, I'm not saving new checkpoints
    #       to same folder. I just want to use that release as a consistent 'initialization' for all my retrain runs
    
    # (also I added a bunch of __init__.py's and a os environ command for tf gpu allow growth in deepspeech.py that are hacky and should be removed)
    
    # ok shit that finished after 2 epochs???
    # alright not sure what's going on with that, but this seems to be the latest/best thread on transfer learning 
    # with deepspeech:https://discourse.mozilla.org/t/non-native-english-with-transfer-learning-from-v0-5-1-model-right-branch-method-and-discussion/42101/18
    
    return None

if __name__ == '__main__':
    train()