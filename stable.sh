#Cleanup
rm raw_out compare changes updates dl_links 2> /dev/null

#Download
curl -H "PRIVATE-TOKEN: $token" 'https://gitlab.com/api/v4/projects/7746867/repository/files/getversion.sh/raw?ref=master' -o getversion.sh && chmod +x getversion.sh
wget -q https://github.com/yshalsager/telegram.sh/raw/master/telegram && chmod +x telegram
wget -q https://github.com/XiaomiFirmwareUpdater/Scripts/raw/master/discord.sh && chmod +x discord.sh

#Check if db exist
if [ -e stable_db ]
then
    mv stable_db stable_db_old
else
    echo "DB not found!"
fi

#Fetch
echo Fetching updates:
cat devices | while read device; do
	codename=$(echo $device | cut -d , -f1)
	android=$(echo $device | cut -d , -f3)
	url=`./getversion.sh $codename F $android`
	tmpname=$(echo $device | cut -d , -f1 | sed 's/_/-/g')
	name=$(echo $device | cut -d '"' -f2)
	echo $tmpname"="$url \"$name\" >> raw_out
done
sed -i 's/param error/none/g' ./raw_out
cat raw_out | sort | sed 's/http.*miui_//' | cut -d _ -f1,2 | cut -d ' ' -f1 | sed 's/-/_/g' > stable_db

#Compare
echo Comparing:
cat stable_db | while read rom; do
	codename=$(echo $rom | cut -d = -f1)
	new=`cat stable_db | grep $codename | cut -d = -f2`
	old=`cat stable_db_old | grep $codename | cut -d = -f2`
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
	model=$(echo $line | cut -d = -f2 | cut -d / -f5 | cut -d _ -f2)
	codename=$(echo $line | cut -d = -f1 | cut -d - -f1)
	version=$(echo $line | cut -d = -f2 | cut -d / -f4)
	android=$(echo $line | cut -d = -f2 | cut -d / -f5 | cut -d _ -f5 | cut -d . -f1,2)
	link=$(echo $line | cut -d = -f2 | cut -d ' ' -f1)
	size=$(wget --spider $link --server-response -O - 2>&1 | sed -ne '/Length:/{s/*. //;p}' | tail -1 | cut -d '(' -f2 | cut -d ')' -f1)
	./telegram -t $bottoken -c @MIUIUpdatesTracker -M "New stable update available!
	*Device*: $name
	*Product*: $model
	*Codename*: $codename
	*Version*: $version
	*Android*: $android
	*Filesize*: $size
	*Download Link*: [Here]($link)
	@MIUIUpdatesTracker | @XiaomiFirmwareUpdater "
	./discord.sh "New stable update available! \n \n **Device**: $name \n **Product**: $model \n **Codename**: $codename \n **Version**: $version \n **Android**: $android \n **Filesize**: $size \n **Download Link**: <$link> \n ~~                                                     ~~"
done
else
    echo "Nothing to do!" && exit 0
fi

#Push
git add stable_db ; git -c "user.name=$gituser" -c "user.email=$gitmail" commit -m "Sync: $(date +%d.%m.%Y-%R)"
git push -q https://$GIT_OAUTH_TOKEN_XFU@github.com/XiaomiFirmwareUpdater/miui-updates-tracker.git HEAD:stable
