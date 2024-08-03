# claudesh

Giving Anthropic's Claude 3.5 model root access to Ubuntu inside of Docker so it can do nifty things.

## Initial setup

1. Make sure you have Docker installed.

2. Create a file `.env` at the root of the repository containing your Anthropic API key:

    ````
    ANTHROPIC_API_KEY=<paste your API key here>
    ````

## Usage

claudesh runs inside of a Docker container; your host machine is safe. The `task` directory of this
repo gets mounted into the container, so you can put files in there for claudesh to work against.
There is an example task included; try out the following prompt:

````sh
$ ./start.sh "Convert the .pdf file to .html and give it a better filename based on the contents. Remove intermediate files."
````

If you have a more elaborate prompt, create a file `./task/instructions.txt` and invoke claudesh
like this instead:

````sh
$ ./start.sh "Read instructions.txt and execute the request it contains."
````

(An example `instructions.txt` is provided.)