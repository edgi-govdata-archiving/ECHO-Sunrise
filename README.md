 [![Code of Conduct](https://img.shields.io/badge/%E2%9D%A4-code%20of%20conduct-blue.svg?style=flat)](https://github.com/edgi-govdata-archiving/overview/blob/master/CONDUCT.md)

# ECHO-Sunrise
Partnership between EDGI's Environmental Enforcement Watch and Sunrise Boston hubs exploring environmental violations, penalties, and injustices in Massachusetts, using EDGI's mirror of the EPA's ECHO database and a customized, Jupyter Notebook-based analysis.

## How to start contributing to this repo
* Contact @ericnost, @crgreenleaf, or other contributors listed below!
* Slack channel - #eew_coordination
* Check out our [good-first-issue](https://github.com/edgi-govdata-archiving/ECHO-Sunrise/labels/good%20first%20issue)s label

## Using Github Issues
* An issue is something specific and resolvable, like a task or a question
* Github Issues can be accessed from the Issues tab
* Usually, the first message in the Issue says what needs resolving and provides any supporting information. Anyone can then comment on the issue to add to the conversation
* Github issues are typically public but not formal—somewhere between an email and a chat message. It is ok to jump in to a conversation in a Github issue if you have something to add
* If you are working on an issue, it is good form to assign yourself to the issue, to comment and say so, and to provide updates (as comments), especially if you are blocked, have a question, or don't have time to work on it anymore
* By default, anyone who has contributed to or been tagged with their Github handle in that issue will receive notifications about updates to that issue. You can see your notifications by clicking on the bell icon in the top right of any Github page (if you're signed in), so this is a good way to stay engaged with a conversation

## Contributors
| Name | Github | Org | 
| ------|--------|--|
| Sara Wylie | @saraannwylie | EEW |
| Lourdes Vera | @lourdesvera | EEW |
| Casey Greenleaf | @crgreenleaf | EEW |
| Steve Hansen | @shansen5 | EEW |
| Eric Nost | @ericnost  | EEW |
| Kelsey Breseman | @Frijol | EEW |
| Dietmar Offenhuber | @dietoff | EEW |
| Gaby Trudo| @gabrielletrudo | EEW |

# Default branch - 'main'
The 'master' branch is no longer the repo's primary branch in line with EDGI's policy decided here: https://github.com/edgi-govdata-archiving/overview/issues/241

> If someone has a local clone, they can update their locals like this:
```
$ git checkout master
$ git branch -m master main
$ git fetch
$ git branch --unset-upstream
$ git branch -u origin/main
$ git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main
```
> The above steps accomplish:
> - Go to the master branch
> - Rename master to main locally
> - Get the latest commits from the server
> - Remove the link to origin/master
> - Add a link to origin/main
> - Update the default branch to be origin/main

(From @jywarren at Public Lab: https://github.com/publiclab/plots2/issues/8077)

---

## License & Copyright

Copyright (C) <year> Environmental Data and Governance Initiative (EDGI)
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 3.0.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

See the [`LICENSE`](/LICENSE) file for details.
