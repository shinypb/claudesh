#!/usr/bin/env python3
import re
import os
import sys
import subprocess

from anthropic import Anthropic, APITimeoutError
# from anthropic.types import TextBlock

import subprocess
import threading
import time

import subprocess
import threading

def run_bash_code(bash_code):
    # Append 'pwd' command to fetch the current directory separately
    # Enclose the initial command(s) in curly braces to ensure they're treated as one block
    bash_code_with_cwd = f"{{ {bash_code}; }}; echo '::CWD::'$(pwd)"
    process = subprocess.Popen(
        bash_code_with_cwd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        executable='/bin/bash'
    )

    def target():
        nonlocal stdout, stderr, exit_code
        stdout, stderr = process.communicate()
        exit_code = process.returncode

    stdout, stderr, exit_code = None, None, None
    thread = threading.Thread(target=target)
    thread.start()
    thread.join(30)  # Wait for 10 seconds

    if thread.is_alive():
        process.terminate()
        thread.join()
        return "", "command took too long", -1, None

    # Decode outputs with error handling
    def decode_output(output):
        try:
            return output.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return output.decode('iso-8859-1')
            except UnicodeDecodeError:
                return output.decode('utf-8', errors='replace')

    stdout_decoded = decode_output(stdout)
    stderr_decoded = decode_output(stderr)

    # Extract the current working directory from the output
    # Find the marker and split the stdout into actual output and cwd
    cwd_marker = "::CWD::"
    if cwd_marker in stdout_decoded:
        output, current_working_directory = stdout_decoded.split(cwd_marker)
    else:
        output = stdout_decoded
        current_working_directory = None

    # Remove any trailing newlines from output and cwd for cleaner results
    output = output.strip()
    if current_working_directory:
        current_working_directory = current_working_directory.strip()

    return output, stderr_decoded, exit_code, current_working_directory

def prefixed_print(prefix, message):
    print("\n".join([
        f"{prefix}: {line}"
        for line in message.split("\n")
    ]))

class Claudesh:
    def __init__(self, client):
        self.client = client
        self.messages = []

    def append_message(self, content):
        prefixed_print("USER", content)
        self.messages.append(
            {
                "role": "user",
                "content": content,
            }
        )

    def get_next_response(self, allow_retry=True) -> str:
        print("?", file=sys.stderr)

        try:
            response = self.client.messages.create(
                max_tokens=4096,
                messages=self.messages,
                model="claude-3-5-sonnet-20240620",
            )
        except APITimeoutError as e:
            if allow_retry:
                print("timeout, retrying", file=sys.stderr)
                return self.get_next_response(allow_retry=False)
            raise e

        print(".", file=sys.stderr)

        # TODO: check response.stop_reason and if it's max_tokens, send another message
        reply = response.content[0].text.strip()

        prefixed_print("CLAUDE", reply)

        self.messages.append({"role": "assistant", "content": reply})
        return reply


def main():
    if len(sys.argv) <= 1:
        print("usage: claudesh <prompt>", file=sys.stderr)
        exit(1)

    prompt = " ".join(sys.argv[1:])

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=30)
    claudesh = Claudesh(client)

    claudesh.append_message(f"""
- You are directly controlling a bash prompt, and will be given a task to complete. Complete the
  task using bash and other Linux commands, as if you were a human user sitting in front of a
  terminal.
- Each of your responses should contain a single command. If solving the task requires running more
  than one command, wait for my next message before giving me the next command.
- Emit a single command before stopping and waiting for its output. e.g. If you first have to install
  something before using it, that should be two separate completion API calls to your model.
- Your output will be executed directly; any non-command output should be prefixed with a # so it is
  interpreted as a comment.
- I repeat: anything you emit will be interpreted as a bash command, so prefix all conversational
  output with # characters so they are interpreted as comments.
- You may look around with ls, find, pwd, cd, and any other commands you like.
- You may install software with apt get.
- You are running as root, so be careful.
- Respond with a single step at a time. I will run the commands sequentially and give you each of
  their outputs.
- Explain your chain of thought in a comment before your command.
- Only respond with the very next step. With the exception of piping commands together, return only
  a single command to be run next.
- After each of your responses, I will respond by giving you an XML-like structure <result>
  containing <stdout>, <stderr>, and <exitcode> blocks.
- When you have completed the task successfully, emit a final message wrapped in <claude-conclusion>
  containing the result.
- Your immediate next message MUST NOT contain <claude-conclusion>.

Here is an example of the sort of task you will receive:
count the number of lines in the file foo.txt that contain the word dog

Here is an example of good output for that prompt:
# First we'll use grep to search foo.txt for lines containing "dog", and then we'll pipe that output
# to wc -l, which will count the number of lines it reads from stdin. Both of these commands are
# pre-installed, so I don't need to install any software.
grep dog foo.txt | wc -l</Claude>

I will respond with this:
<response><stdout>14</stdout><stderr></stderr><exitcode>0</exitcode></response>

You will respond with:
<claude-conclusion>14</claude-conclusion>

This concludes your instructions. What follows is your task, which you should begin working on now:
{prompt}
""")

    MAX_MESSAGES = 100
    while len(claudesh.messages) < MAX_MESSAGES:
        resp = claudesh.get_next_response()
        if "<claude-conclusion>" in resp:
            print("\nConclusion:")
            result = re.search(r"<claude-conclusion>(.*?)</claude-conclusion>", resp, re.DOTALL)
            if result:
                print(result.group(1))

            exit()

        stdout, stderr, exitcode, cwd = run_bash_code(resp)
        prefixed_print("BASH", f"exit code {exitcode}, cwd {cwd}")
        prefixed_print("BASH STDOUT", stdout)
        prefixed_print("BASH STDERR", stdout)
        
        if cwd is not None:
            os.chdir(cwd)


        claudesh.append_message(f"""<result><stdout>{stdout}</stdout><stderr>{stderr}</stderr><exitcode>{exitcode}</exitcode></result>""")




if __name__ == "__main__":
    main()
