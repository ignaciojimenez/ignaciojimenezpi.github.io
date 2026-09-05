## New features
- Is there any way in which people could subscribe to my albums? I.e. get notified when a new album is added? Honeslty I think the interest will be incredibly low, but it's something to consider. Initially I can only think of my mom and dad as potential subscribers, but likely they'd like it in their phone via whatsapp or similar more traditional means. An rss feed would be a good alternative but I doubt it will be useful for them - but maybe other people would.

- Create a blog/writing section where I can write about stuff - mostly work/leadership related but regardless. A good inspiration in regards to article formatting, and etc is https://lalitm.com. I like the simplistic flow. It should 100% include a way for readers to follow it using rss readers like feedly, common in my industry. Style should follow rigorously the same as the rest of the website, adapting the functionality ideas from the blog above.

## Fix

## Improve
- Space management: Right now we have many versions of the pictures to provide a very varied set of formats suitable for different devices. However, this likely contributes to space consumption. What would be a good compromise keeping both high quality, space usage and also speed of loading in mind?

- Optimizations for performance? Specially when loading each album it sometimes feels a bit slow

## Misc
- Recover backup after old commit cleanup if neccesary
```
cd /Users/choco/Documents/Workspaces
rm -rf ignaciojimenezpi.github.io
git clone ignaciojimenezpi.github.io-backup-20251127-093123.bundle ignaciojimenezpi.github.io
cd ignaciojimenezpi.github.io
git remote add origin https://github.com/ignaciojimenez/ignaciojimenezpi.github.io.git
```