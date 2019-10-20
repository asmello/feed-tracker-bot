# source-bot
A Telegram bot that tracks your RSS/Atom feeds for you.

## Notice
Under initial development. Use at your own peril.

# Requirements

### Python packages:
- [feedparser](https://github.com/kurtmckee/feedparser)
- [sqlalchemy](https://www.sqlalchemy.org/)
- [psycopg2](http://initd.org/psycopg/)
- [python-telegram-bot](https://python-telegram-bot.org/)
- [pyyaml](https://pyyaml.org/)

### External dependencies:
- A working PostgreSQL database

## TODO
- Make into a pip package
- Complete user management
- Expand feed metadata
- Complete feed management
- Add filtering rules
- Chat management
- Add more source types
- Switch to webhook
- DB cache layer?
