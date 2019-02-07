WORKDIR=/home/jomoon/jansible/j-greenplum
cd $WORKDIR
for i in `grep -rn "ansible_distribution != 'CentOS' and ansible_distribution != 'Red Hat Enterprise Linux'" . | cut -f 1,2 -d ':'`
do
    NUM=${i#*:}
    FILENAME=${i%:*}
    # echo $NUM
    # echo $FILENAME
    # sed -i -e "s/ansible_distribution == 'CentOS' or ansible_distribution == 'Red Hat Enterprise Linux'/ansible_os_family == 'RedHat'/g" $WORKDIR/$FILENAME
    sed -i -e "s/ansible_distribution != 'CentOS' and ansible_distribution != 'Red Hat Enterprise Linux'/ansible_os_family != 'RedHat'/g" $WORKDIR/$FILENAME
done
