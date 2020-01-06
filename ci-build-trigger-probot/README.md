CI Build Trigger (WIP)
======================

This is a short [Probot](https://probot.github.io/) script to invoke CI jobs for pull requests.

Usage: Include the line
```
/ci okay to test
```
anywhere in a comment to the pull request, and the bot will invoke the CI job (\*)

\* Not yet. For now, the script will only emit the message `Adding PR XXX to whitelist...` and won't do anything. TODO: Use JS AWS SDK to add the PR to a DB table.

How to run
==========
1. Install Node.js dependencies
```
npm install --save nodemon probot smee-client probot-commands
```
2. Follow steps in [the section titled "Manually Configuring a GitHub App"](https://probot.github.io/docs/development/#manually-configuring-a-github-app).
3. Run `npm start`.
