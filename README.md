WorkInProgress
==============
## New users
 1. Clone repository
 2. Checkout master branch
 3. Copy the file pre-push to .git/hooks/
 
Current PROJECTMASTER branches:
 * HDTV
 * CompressedSensingDWI
 * MattToewsFeatures
 * ForbesThesis

### Creating a new branch for a project:
Name format: PROJECTMASTER.BRANCHNAME where PROJECTMASTER is the name of the project (i.e. 'HDTV')

### Creating the master branch for a project (no previous history):
```bash
git checkout --orphan <PROJECTMASTER>
git push origin <PROJECTMASTER>:<PROJECTMASTER>
```

### Creating the master branch for a project (with Git remote):
```bash
git remote add tmp
git fetch tmp
git checkout tmp/master
git checkout -b <PROJECTMASTER>
git push origin <PROJECTMASTER>:<PROJECTMASTER>
git remote remove tmp
git checkout master
git branch -D tmp/master
```


