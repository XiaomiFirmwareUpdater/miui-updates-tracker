#Cleanup
rm raw_out compare changes updates dl_links 2> /dev/null

#Download
curl -H "PRIVATE-TOKEN: $token" 'https://gitlab.com/api/v4/projects/7746867/repository/files/fastboot.sh/raw?ref=master' -o fastboot.sh && chmod +x fastboot.sh
wget -q https://github.com/yshalsager/telegram.py/raw/master/telegram.py
wget -q https://github.com/XiaomiFirmwareUpdater/Scripts/raw/master/discord.sh && chmod +x discord.sh

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
	name=$(echo $device | cut -d '"' -f2)
	echo $tmpname"="$url \"$name\" >> raw_out
done
sed -i 's|=//|=none|g' ./raw_out
cat raw_out | sort | sed 's|http://bigota.d.miui.com/V[0-9]*.[0-9]*.[0-9]*.[0-9]*.[A-Z]*/||g' | sed 's/_[0-9]*.[0-9]*.[0-9]*_[0-9]*.[0-9]*_[a-z]*_[a-z0-9]*.[a-z]*//g' | cut -d ' ' -f1 | sed 's/-/_/g' > stable_fastboot_db

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

if [ -s dl_links ]
then
#Telegram
cat dl_links | sed -n '/none/!p' | while read line; do
	name=$(echo $line | cut -d '"' -f2)
	codename=$(echo $line | cut -d = -f1 | cut -d - -f1)
	version=$(echo $line | cut -d = -f2 | cut -d / -f4)
	changes=$(echo $line | cut -d ' ' -f2)
	md5=$(echo $line | cut -d ' ' -f3)
	size=$(echo $line | cut -d ' ' -f4)
	android=$(echo $line | cut -d ' ' -f5)
	link=$(echo $line | cut -d = -f2 | cut -d ' ' -f1)
	python telegram.py -t $bottoken -c @MIUIUpdatesTracker -M "New stable fastboot image available!
	*Device*: $name
	*Codename*: $codename
	*Version*: $version
	*Android*: $android
	*Filesize*: $size
	*MD5*: $md5
	*Changelog*: [Here]($changes)
	*Download Link*: [Here]($link)
	@MIUIUpdatesTracker | @XiaomiFirmwareUpdater"
	./discord.sh "New stable fastboot image available! \n \n **Device**: $name \n **Codename**: $codename \n **Version**: $version \n **Android**: $android \n **Filesize**: $size \n **MD5**: $md5 \n **Changelog**: <$changes> \n **Download Link**: <$link> \n ~~                                                     ~~"
done
else
    echo "Nothing to do!" && exit 0
fi

#Push
git add stable_fastboot_db ; git -c "user.name=$gituser" -c "user.email=$gitmail" commit -m "Sync: $(date +%d.%m.%Y-%R)"
git push -q https://$GIT_OAUTH_TOKEN_XFU@github.com/XiaomiFirmwareUpdater/miui-updates-tracker.git HEAD:stable_fastboot
