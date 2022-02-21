# Troubleshooting

## 1. pytz.exceptions.UnknownTimeZoneError: 'Can not find any timezone configuration'

It is a common problem in Ubuntu, the solution is setting the locale environment variable correctly, e.g.
```
export TZ=America/Indiana/Indianapolis
```

## 2. ValueError: unknown locale: UTF-8

You may meet this error with earlier version of Python, please set the environment variables like below.

```text
export LANGUAGE=en_US.UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LC_CTYPE=en_US.UTF-8
export LC_MESSAGES=en_US.UTF-8
```