# iot-project-2020
## Windows 10 setup
* Download git: [Git install tutorial](https://phoenixnap.com/kb/how-to-install-git-windows)
* Download and install docker: [Docker installer](https://hub.docker.com/editions/community/docker-ce-desktop-windows/)
* Set the environment variable: [Env variable tutorial](https://phoenixnap.com/kb/windows-set-environment-variable). The variable names you have to set are (the key values must asked to @MatteoBattilana):
  - OPENWETHERMAPAPIKEY
  - THINGSPEAKAPIKEY
* Clone the project repository to your computer:
  - Open the git bash just installed
  - Write the following command: `git clone https://github.com/MatteoBattilana/iot-project-2020.git`
* In order to start the architecture you have to:
  - Enter the service directory: `cd iot-project-2020/services`
  - Start the architecture (it will take a while): `docker-compose up`

Once the log messages are showing, the infrastructure is running and the web interface of node-red will be visible at: [http://localhost/ui](http://localhost/ui) 

### Fix node-red problem
You should enter the project directory, open the git bash terminal and execute:
```
git config --global core.eol lf
git config --global core.autocrlf input
```


## GIT commands
### Update the repo to the last update without modification to the same file
```
git fetch
git pull
```


### Create a branch and enter
```
git branch newbranch
git checkout newbranch
```

### Push your changes to GitHub, to your branch
```
git add .
git commit -m "Added servicetest"
git push origin newbranch
```
Once you have done your work, open a pull request using the GitHub interface
