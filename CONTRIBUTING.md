# Contribution Guide

## Establish Development Environment

### Python 3.7

We strongly recommend using [virtualenv](https://virtualenv.pypa.io/en/latest/index.html) or other similar tools for an isolated Python environment in case of dependencies conflict error, e.g.

```shell
pip install virtualenv
virtualenv my_venv --python=python3.7
source my_venv/bin/activate
```

Now you can configure it as the Project Interpreter if you are using PyCharm as your IDE.

### Java (optional)

Java is only required when you are developing Java client API.

## Building From Source
To install AIFlow from source code, you need to have **yarn (1.22.10 or newer)** to compile the frontend of Airflow. Please refer to [Yarn Installation](https://classic.yarnpkg.com/en/docs/install) on how to install yarn. 

Follow these steps to install AIFlow from source code:

1. Clone the repo
   ```
   git clone https://github.com/flink-extended/ai-flow.git
   ```
2. Build AIFlow and install to your workstation. You could run the following commands at the root directory of the source code to install AIFlow:

   ```shell
   cd ai-flow
   sh install_aiflow.sh
   ```

## Run Tests

You can run the shell script `run_tests.sh` to verify the modification of AIFlow. 

If you modified the bundled Airflow, you need to add relevant test cases and run tests according to [Airflow contributing guidelines](../../../lib/airflow/CONTRIBUTING.rst).

## Pull Request Checklist

Before sending your pull requests, make sure you followed this list.

- Open an issue (https://github.com/flink-extended/ai-flow/issues)
- Create a personal fork of the project on Github.
- Clone the fork on your local machine. Your remote repo on Github is called `origin`.
- Add the original repository as a remote called `upstream`.
- If you created your fork a while ago be sure to pull upstream changes into your local repository.
- Create a new branch to work on! Branch from `master`.
- Implement/fix your feature, comment your code.
- Run tests.
- Write or adapt tests as needed.
- Add or change the documentation as needed.
- Create a new branch.
- Push your branch to your fork on Github, the remote `origin`.
- From your fork open a pull request in the correct branch. Go for `master`!
- Wait for approval.
- Once the pull request is approved and merged you can pull the changes from `upstream` to your local repo and delete your extra branches.


## Contact Us

For more information, you can join the **AIFlow Users Group** on [DingTalk](https://www.dingtalk.com) to contact us.
The number of the DingTalk group is `35876083`. 

You can also join the group by scanning the QR code below:

![Alt text](docs/content/images/dingtalk_qr_code.png)
