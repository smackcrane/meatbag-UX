# meatbag-UX


## Usage

* To create survey, create a file \<name\>.yaml under ./surveys/ following the format of test.yaml:


```
questions:
    <query_name>:
        query: <prompt to print>
        options:
            - <list of options to print after prompt>
    teatime:
        query: What time tea?
        options:
            - morning
            - mid-day
            - afternoon
            - evening
    meditation:
        query: How long meditation?
    bike:
        query: How bike today?
    mood:
        query: Mood words?
        options:
            - __past_words__
    tasks:
        query: What tasks did you complete today? (task name is key, start / end is value)
        key-value:

```

  * Options are not enforced, just printed along with the prompt

  * The value under 'options' may be "\_\_past\_\_" to list all past responses as options, or "\_\_past\_words\_\_" to list all words used in past responses as options

  * Including `daily` as a `query_name` tells meatbag to treat it as a daily survey---filling out the survey a second time in the same day will edit (and overwrite) the previous.
  
  * Data from survey is saved at ./data/\<name\>.csv
  
* To visualize data in calendar format:


```
> python3 -i DataCalendar.py
>>>
>>>
```


## Install

Here's an example script that will create a symbolic link for 'bag' command

```bash
cd ~/projects/meatbag-ux
path_loc=/usr/local/bin
ln -s ./bag.py $path_loc/bag
```

On the other hand, if for some reason you'd like to wrap it in bash:

```bash
cd ~/projects/meatbag-ux
path_loc=/usr/local/bin
cat <<EOF >$path_loc/bag
#!/bin/bash
python3 $PWD/bag.py \$@
EOF
chmod +x $path_loc/bag
```




