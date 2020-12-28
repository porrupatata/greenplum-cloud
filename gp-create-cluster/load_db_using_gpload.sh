HOST=$1
DB=xxxxxxx
FOLDER=/data_files

## create tables from ddl dumps
for folderFILE in $FOLDER/ddl/*ddl.dmp
do
	FILE=`echo $folderFILE | sed 's/^.*ddl\///g'`
	echo $FILE
	psql -h $HOST -p 5432 -d $DB -U gpadmin -f $folderFILE > "$FOLDER/log/$FILE.log" 2>&1 
        	
done

## copy/move table data csv files to master
for folderFILE in $FOLDER/*csv.gz
do
	echo -e " copying $folderFILE to GP MASTER "
	scp -i xxxxxxx.pem.ppk "$folderFILE" gpadmin@"$HOST":/data/xxxxxx/  
done

## copy/move yaml conf files and script for gpload to master
scp -i xxxxxxx.pem.ppk -r $FOLDER/gpload_yamls gpadmin@"$HOST":/data/xxxxx/ 

## execute gpload script to load all files 
ssh -i xxxxxxx.pem.ppk gpadmin@"$HOST" '/data1/data_files/gpload_yamls/gpload_files_in_folder.sh' 
 
