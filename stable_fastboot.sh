#Cleanup
rm raw_out compare changes updates dl_links 2> /dev/null

#Check if db exist
if [ -e stable_fastboot_db ]
then
    mv stable_fastboot_db stable_fastboot_db_old
else
    echo "DB not found!"
fi

#Fetch
echo Fetching updates:
cat devices | while read device; do
	codename=$(echo $device | cut -d , -f1)
	region=$(echo $device | cut -d , -f3)
	url=`bash fastboot.sh $codename F $region`
	tmpname=$(echo $device | cut -d , -f1 | sed 's/_/-/g')
	echo $tmpname"="$url >> raw_out
done
sed -i 's\http.*com//\not avilable\g' ./raw_out
sed -i 's/^ *//; s/ *$//; /^$/d' ./raw_out
cat raw_out | sort | sed 's\http.*/\\' | sed 's/_[0-9]*.[0-9]*.[0-9]*_[0-9]*.[0-9]*_[a-z]*_[a-z0-9]*.[a-z]*//g' | sed 's/-/_/g' > stable_fastboot_db

#Compare
echo Comparing:
cat stable_fastboot_db | while read rom; do
	codename=$(echo $rom | cut -d = -f1)
	new=`cat stable_fastboot_db | grep $codename | cut -d = -f2`
	old=`cat stable_fastboot_db_old | grep $codename | cut -d = -f2`
	diff <(echo "$old") <(echo "$new") | grep ^"<\|>" >> compare
done
awk '!seen[$0]++' compare > changes

#Info
if [ -s changes ]
then
	echo "Here's the new updates!"
	cat changes | grep ">" | cut -d ">" -f2 | sed 's/ //g' 2>&1 | tee updates
else
    echo "No changes found!"
fi

#Downloads
if [ -s updates ]
then
    echo "Download Links!"
	for rom in `cat updates | cut -d = -f2`; do cat raw_out | grep $rom ; done 2>&1 | tee dl_links
else
    echo "No new updates!"
fi

#Telegram
cat dl_links | while read line; do
	model=$(echo $line | cut -d = -f2 | cut -d / -f5 | cut -d _ -f2)
	codename=$(echo $line | cut -d = -f1)
	version=$(echo $line | cut -d = -f2 | cut -d / -f4)
	android=$(echo $line | cut -d = -f2 | cut -d / -f5 | cut -d _ -f5 | cut -d . -f1,2)
	link=$(echo $line | cut -d = -f2)
	./telegram -t $bottoken -c $chat -M "New fastboot image available!
	*Device*: $codename
	*Version*: $version
	*Android*: $android
	*Download Link*: [Here]($link)
	@MIUIUpdatesTracker | @XiaomiFirmwareUpdater"
done

#Push
git config --global user.email "$gitmail"; git config --global user.name "$gituser"
git add stable_fastboot_db; git commit -m "Sync: $(date +%d.%m.%Y)"
git push -q https://$GIT_OAUTH_TOKEN_XFU@github.com/XiaomiFirmwareUpdater/miui-updates-tracker.git HEAD:stable_fastboot
