echo -n 'enter your original file: '
read original
echo -n 'your original file md5sum is: '
md5_ori=sudo md5sum $original | awk '{ print $1 }'

echo -n 'enter your downloaded file: '
read downloaded
echo -n 'your downloaded file md5sum is: '
md5_download=sudo md5sum $downloaded | awk '{ print $1 }'

if [ $md5_ori == $md5_download ] 
then
  echo 'md5sum is equal'
  exit
fi

echo -e 'md5sum is not equal'