#!/bin/bash
JENKINS_URL=http://10.10.10.10:8888
JENKINS_USERNAME=maxwell
JENKINS_PASSWORD=123123

job_name_list=(Job1 Job2 Job3)

cd $WORKSPACE
rm -rf $WORKSPACE/*

#pip install tabulate
cp -r ~/python_tools/* $WORKSPACE/
Code_Repo="https://gerrit.maxwell.com/gerrit/a/test-repo"
rm -rf test-repo && git clone ${Code_Repo}


python3 get_job_config.py "${JENKINS_URL}" "${JENKINS_USERNAME}" "${JENKINS_PASSWORD}" ${job_name_list[*]}

echo "################################################################################################################################################################"

for job_name in ${job_name_list[@]}; do
    rm -rf ${job_name}.xml
    job_url="${JENKINS_URL}/job/${job_name}/config.xml"
    curl -sS --user ${JENKINS_USERNAME}:${JENKINS_PASSWORD} -X GET $job_url -o ${job_name}.xml
    sed -i '1d' ${job_name}.xml
    sed -i '1i\<project>' ${job_name}.xml
    job_env=$(xmllint --xpath '//builders/hudson.tasks.Shell/command' ${job_name}.xml | sed 's/<\/\?command\/\?>//g' | sed -n '/run_test/p' | awk '{print $2}')
    echo "#### ${job_name}'s ENV: ${job_env}"
    xmllint --xpath '//builders/hudson.tasks.Shell/command' ${job_name}.xml | sed 's/<\/\?command\/\?>//g' | sed -n '2,/run_test/p' | nl -b t
    echo "################################################################################################################################################################"
done
