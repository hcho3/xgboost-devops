/**
 * This is the main entrypoint to your Probot app
 * @param {import('probot').Application} app
 */

const commands = require('probot-commands')

module.exports = app => {
  // Your code here
  app.log('Yay, the app was loaded!')

  commands(app, 'ci', (context, command) => {
    const { comment, issue, pull_request: pr } = context.payload
    const user = (comment || issue || pr).user.login
    app.log(`User: ${user}, Args: ${command.arguments}`)
    if (command.arguments === 'okay to test') {
      if (issue) {
        const linked_pr = issue.pull_request
        if (linked_pr) {
          const params = context.repo()
          app.log(`Repo ${params.repo} owned by ${params.owner}`)
          context.github.repos.getCollaboratorPermissionLevel({
            owner: params.owner,
            repo: params.repo,
            username: user
          }).then(function(r) {
            app.log(`Commentor has permission: ${r.data.permission}`)
            if (r.data.permission === 'admin' || r.data.permission === 'write') {
              app.log(`Adding PR #${issue.number} to whitelist...`)
            }
          })
        }
      }
    }
  });

  // For more information on building apps:
  // https://probot.github.io/docs/

  // To get your app running against GitHub, see:
  // https://probot.github.io/docs/development/
}
