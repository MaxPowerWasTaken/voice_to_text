# How I set this up from scratch

## DeepSpeech prerequisites
- install cuda 10.0 and cudnn 7.5 (for use on gpu) via []

## set up blank repo
`mkdir voice_to_text && cd voice_to_text`

## add DeepSpeech repo as vendor'd requirement via git subtree
Why add whole repo instead of adding dep to pipfile?
https://github.com/mozilla/DeepSpeech/issues/2219

`git init && touch README.md`
`git add README.md && git commit -m 'initial commit'`
`git subtree add --prefix vendor/DeepSpeech https://github.com/mozilla/DeepSpeech.git master --squash`

^ Per DeepSpeech Readme's instructions for cloning that repo, installing [Git Large File Storage](https://git-lfs.github.com/) first is a pre-requisite.

### PSYCHE - no using gitsubtree...
DeepSpeech uses git-lfs which doesn't work with git-subtrees https://discourse.mozilla.org/t/problems-trying-to-run-model-inference-from-ds-repo-clone-without-pip-install/42199/5?u=mepstein68

Instead, I use the following commands (from `~/voice_to_text`) to get DeepSpeech vendored repo:
`DS_COMMIT_HASH=4b29b78832036216b53f59b953639bde7cde7dfe`  # release 0.5.1, the latest release we have a pretrained english model for (as of 7/8/2019)
`mkdir vendor && cd vendor`
`wget https://github.com/mozilla/DeepSpeech/archive/$DS_COMMIT_HASH.zip`
`unzip $DS_COMMIT_HASH.zip`
`mv DeepSpeech-$DS_COMMIT_HASH DeepSpeech`  # (mv as rename)
`rm $DS_COMMIT_HASH.zip`
(to confirm the your DS version here, you can `cat DeepSpeech/VERSION`)

...so now we have a copy of DeepSpeech repo in vendor/, but we still need to download the pretrained
English model. Execute the following commands from `vendor/DeepSpeech/`:
`wget https://github.com/mozilla/DeepSpeech/releases/download/v0.5.1/deepspeech-0.5.1-models.tar.gz`
`tar xvfz deepspeech-0.5.1-models.tar.gz`
`rm deepspeech-0.5.1-models.tar.gz`
`mv deepspeech-0.5.1-models models-0.5.1`  # renaming models folder, personal preference

### Problems with git-lfs persist...
after creating a barebones github repo, setting it as my `upstream` for my local `voice_to_text` repo and running
`git push -u origin master`, I got the following error:

```
remote: Resolving deltas: 100% (682/682), done.
remote: error: GH008: Your push referenced at least 3 unknown Git LFS objects:
remote:     e1fa6801b25912a3625f67e0f6cafcdacb24033be9fad5fa272152a0828d7193
remote:     a5324f06b27c7b4ef88dd2c8bc3d05d4c718db219c2e007f59061a30c9ac7afa
remote:     1991108e83cf86830cad118ac9e061aadfc89b73a909a66fe1755f846def556e
remote: Try to push them with 'git lfs push --all'.
To github.com:MaxPowerWasTaken/voice_to_text.git
 ! [remote rejected] master -> master (pre-receive hook declined)
error: failed to push some refs to 'git@github.com:MaxPowerWasTaken/voice_to_text.git'
```
ok so tried `git lfs push --all` and then `git push origin master`. same error as above.

ok so there's no `.git` file in `vendor/DeepSpeech` (although there is a `.github`), but 
running `ls -a .git` from `voice_to_text` showed an `lfs` folder with three entries in `lfs/objects`:
`19`, `a5`, `e1`...
which correspond to the three hashes of the "3 unknown git LFS objects" referenced in the error above.
So what if we just `rm -rf .git/lfs`? and then `git push origin master`?
...same error.

ok there's also `.git/hooks/` folder with four active hooks (by "active" hooks I mean files in `hooks/`
which don't end in `.sample` - git ignores those according to Steve). `cat`ing each of those hooks
(pre-push, post-commit, post-checkout, post-merge) shoes each one references git-lfs.
So what if we `rm` each of those four lfs-related git hooks and then `git push origin master` again?
...same error.

Also, I found this github thread on same git-lfs error https://github.com/git-lfs/git-lfs/issues/3231
which was very interesting, although I couldn't figure out from it how to fix my problem.
But, it gave me a couple interesting commands to run, input/output below:
```
mepstein@pop-os:~/voice_to_text$ git config --list | grep lfs
filter.lfs.clean=git-lfs clean -- %f
filter.lfs.smudge=git-lfs smudge -- %f
filter.lfs.process=git-lfs filter-process
filter.lfs.required=true
lfs.https://github.com/MaxPowerWasTaken/voice_to_text.git/info/lfs.access=basic
lfs.allowincompletepush=true
mepstein@pop-os:~/voice_to_text$ git lfs ls-files | grep e1fa
e1fa6801b2 - vendor/DeepSpeech/data/lm/lm.binary
mepstein@pop-os:~/voice_to_text$ git lfs ls-files | grep a5324
a5324f06b2 - vendor/DeepSpeech/data/lm/trie
mepstein@pop-os:~/voice_to_text$ git lfs ls-files | grep 1991108e83
mepstein@pop-os:~/voice_to_text$ git lfs ls-files
e1fa6801b2 - vendor/DeepSpeech/data/lm/lm.binary
a5324f06b2 - vendor/DeepSpeech/data/lm/trie
```
interesting...so when I git push, git-lfs complains about 3 unknown files, but `git lfs ls-files` only
shows me two (the lm.binary and the trie)

ok so maybe I should check out `git lfs --help`? Two commands seem potentially promising:
```
       git-lfs-untrack(1)
              Remove Git LFS paths from Git Attributes.
```
and 
```
       git-lfs-uninstall(1)
              Uninstall Git LFS by removing hooks and smudge/clean filter configuration.
```
tried `git-lfs-untrack` [hashes] first but got
```git-lfs-untrack: command not found
mepstein@pop-os:~/voice_to_text$ git-lfs-untrack --help
git-lfs-untrack: command not found
mepstein@pop-os:~/voice_to_text$ git-lfs untrack --help
git lfs untrack <path>...

Stop tracking the given path(s) through Git LFS.  The <path> argument
can be a glob pattern or a file path.
```
so then
```
mepstein@pop-os:~/voice_to_text$ git lfs untrack vendor/DeepSpeech/data/lm/lm.binary
mepstein@pop-os:~/voice_to_text$ git lfs untrack vendor/DeepSpeech/data/lm/trie
```
but it seems to have done nothing:
```
mepstein@pop-os:~/voice_to_text$ git lfs ls-files
e1fa6801b2 - vendor/DeepSpeech/data/lm/lm.binary
a5324f06b2 - vendor/DeepSpeech/data/lm/trie
mepstein@pop-os:~/voice_to_text$ git push origin master
LFS upload missing objects: (0/3), 0 B | 0 B/s                                                
...
remote: error: GH008: Your push referenced at least 3 unknown Git LFS objects:
...```

finally(?):
```
mepstein@pop-os:~/voice_to_text$ git lfs uninstall
Hooks for this repository have been removed.
Global Git LFS configuration has been removed.
```
and then `git push origin master`:
same error. son of a motherfucker.


## Set up Pipenv
`pipenv install --python 3.6 && pipenv shell`
`pipenv install -r vendor/DeepSpeech/requirements.txt`
`pipenv uninstall tensorflow && pipenv install 'tensorflow-gpu==1.13.1'`
`pipenv install $(python3 vendor/DeepSpeech/util/taskcluster.py --decoder)`


## Get the latest English pre-trained model
`cd vendor/DeepSpeech`
`wget https://github.com/mozilla/DeepSpeech/releases/download/v0.5.1/deepspeech-0.5.1-models.tar.gz`
`rm deepspeech-0.5.1-models.tar.gz`

# Using this voice-to-text repo
## Setup
Since all DeepSpeech code and models are vendored inside of this repo, no need to install DeepSpeech separately. Just git clone this repo and run `pipenv shell` to activate the virtual environment.

## Data Prep
Clips currently come in daily by email, in .m4a format, with filename (usually) as transcript. The following data prep steps need to be taken before DeepSpeech training:
    - download clips to voice_to_text/data/audio_raw/
    - ensure each audio's filename is correct transcript (apparently filenames can contain apostrophes / question marks)
    - run `voice_to_text/src/utilities/process_raw_email_clips.py`. this will:
        - scan voice_to_text/data/audio_wav4 and /data/transcripts to get latest file incrementer (or throw error that data files out of sync): `latest_i`
        - start a counter `i` from `latest_i` to `latest_i` + num-files-in-audio_raw. for each (in arbitrary order):
            - get filename (.name of Path object) `text` and write that `text` to /data/transcripts/t{i}.txt
            - rest is basically what's already done in `repeat_after_mom/scripts/convert_audio_m4a_to_wav4.py`
                -   from pydub import AudioSegment
                    from pathlib import Path

                    for f in Path('audio_raw').glob('*.m4a'):
                        voice_clip = AudioSegment.from_file(f, format="m4a")
                        filename = f.name.split('.')[0]
                        voice_clip.export(out_f = f'audio_wav4/{filename}.wav4', format='wav')

## run inference using a new checkpoint model
DS=vendor/DeepSpeech
python $DS/DeepSpeech.py --model models_retrained_1/best_dev_checkpoint --alphabet $DS/deepspeech-0.5.1-models/alphabet.txt --lm $DS/deepspeech-0.5.1-models/lm.binary --trie $DS/deepspeech-0.5.1-models/trie  --audio "/home/mepstein/voice_to_text/data/audio_wav4/a24.wav4"



APPENDIX / notes on git subtree...
initially tried git subtree add command above before making any commits and got...
ERROR:
```fatal: ambiguous argument 'HEAD': unknown revision or path not in the working tree.
Use '--' to separate paths from revisions, like this:
'git <command> [<revision>...] -- [<file>...]'
Working tree has modifications.  Cannot add.
```

ok...
`mkdir vendor`
`git subtree add --prefix vendor/DeepSpeech https://github.com/mozilla/DeepSpeech.git master --squash`
...same error

after googling, appears maybe problem is my current repo has no commits? try committing this (in progress README.md (**inception**) and try subtree add again...
`rm -rf vendor`
`git add README.md`
`git commit -m 'initial commit'`
Success!
```
git fetch https://github.com/mozilla/DeepSpeech.git master
warning: no common commits
remote: Enumerating objects: 25, done.
remote: Counting objects: 100% (25/25), done.
remote: Compressing objects: 100% (19/19), done.
remote: Total 9791 (delta 10), reused 17 (delta 6), pack-reused 9766
Receiving objects: 100% (9791/9791), 40.69 MiB | 21.12 MiB/s, done.
Resolving deltas: 100% (6206/6206), done.
From https://github.com/mozilla/DeepSpeech
 * branch            master     -> FETCH_HEAD
Added dir 'vendor/DeepSpeech'
```

`ls`
`README.md  vendor`

`ls vendor`
```
mepstein@pop-os:~/voice_to_text2$ ls vendor
DeepSpeech
```

`git log --oneline`
```
77421e3 (HEAD -> master) Merge commit 'c77ec4b29689865aae33f61f6fbfd6a0837909a5' as 'vendor/DeepSpeech'
c77ec4b Squashed 'vendor/DeepSpeech/' content from commit c45c70c
a9fe4cd initial commit
```