🎓 *UniPulse — User Guide*

Never miss a campus event again. UniPulse is your single, hashtag-driven feed for NUS life — events posted across any group chat, surfaced straight to you.

---

🚀 *Getting Started (One-Time Setup)*

1. *Verify your NUS identity:* Send /verify in a DM with the bot.
2. *Enter your NUS email:* The bot will ask for an email ending in @u\.nus\.edu or @nus\.edu\.sg\.
3. *Click the magic link:* Check your inbox (and spam\!) and tap the verification link\.
4. *Pick your interests:* You'll be shown a list of categories \(#sports, #tech, #arts, …\)\. Subscribe to the ones you care about\.

That's it\! Events in your categories will start appearing in your daily digest\.

---

📋 *Browsing Events*

*1\. See Upcoming Events*
Send /events to see the next 10 upcoming events, sorted by date\.
Each event card shows:
• Title, date, location, and description
• Total RSVP count
• Buttons to RSVP, set a reminder, add to Google Calendar, or share

*2\. See What's Trending*
Send /trending to see the top 5 events ranked by RSVP count\.
Great for finding out what everyone's excited about\.

*3\. Search for Events*
/find \<keyword\> — search by text \(e\.g\. /find hackathon\)
/find \#category — filter by category \(e\.g\. /find \#sports\)

---

🙋 *RSVPs & Reminders*

*RSVP to an Event*
Tap *RSVP 🙋 \(N\)* on any event card to mark yourself as attending\. Tap again to cancel\.

*Get Reminded*
Tap *⏰ Remind Me* on any event card\. The bot will DM you:
• 24 hours before the event
• 1 hour before the event

You can also RSVP first — reminders are created automatically\.

*Add to Google Calendar*
Tap *📅 Add to Calendar* to open Google Calendar with the event pre\-filled\.

*Share an Event*
Tap *🔗 Share* to get a deep link you can forward to friends\. They'll be taken straight to the event card when they tap it\.

---

🔔 *Subscriptions & Newsletter*

*Subscribe to Categories*
Send /subscribe to open the category menu\. Tap any category to toggle it on/off — a checkmark \[x\] means you're subscribed\.

Categories are created automatically when events are posted \(e\.g\. if someone posts \#unipulse \#workshop, the "workshop" category appears\)\.

*Daily Digest*
You'll receive a personalised digest once a day with upcoming events from your subscribed categories\.

Set the time you want to receive it:
/newslettertime 09:00 \(uses Singapore Time\)

Default delivery time is 9:00 AM SGT\.

*Weekly Roundup*
Every Sunday at 6 PM SGT, UniPulse sends the top 10 events of the week ranked by RSVPs — even if you have no category subscriptions\.

---

📢 *Posting an Event \(Verified Users Only\)*

To add an event to the feed:

1\. Make sure the bot is a member of your group chat\.
2\. Post your event announcement with *\#unipulse* in the message\.
3\. Add extra hashtags to set the category \(e\.g\. \#unipulse \#sports\)\.
4\. Optionally attach an image poster — the bot will OCR it for missing details\.

*Example:*
```
Hackathon Night @ UTown Auditorium
Date: 15 March, 6 PM
Open to all students!

#unipulse #tech #hackathon
```

The bot will automatically extract the title, date, location, and description using AI and post a formatted event card back to the group\.

*Limits:* 5 posts per hour per user\.

---

⚙️ *Managing Your Posts*

Send /manage to see all events you've posted, including:
• *✏️ Edit* — fix any AI parsing errors \(title, date, location, or description\) field\-by\-field
• *🗑 Delete* — soft\-delete an event \(it disappears from all feeds\)

You can also use:
/edit \<event\_id\> — edit a specific event directly
/delete \<event\_id\> — delete a specific event directly

---

⚙️ *Commands Reference*

/start — Welcome screen \(shows onboarding on first login\)
/verify — Verify your NUS identity via email magic link \(DM only\)
/events — Browse upcoming events \(chronological\)
/trending — Browse events by popularity
/find \<query\> — Search by keyword or \#category
/subscribe — Manage your category subscriptions
/newslettertime HH:MM — Set your daily digest time \(SGT\)
/manage — View, edit, and delete your own posts
/edit \<event\_id\> — Edit an event field\-by\-field
/delete \<event\_id\> — Remove an event from the feed
/help — Show this guide

---

💡 *Pro Tips*

• *No categories yet?* They're created automatically when events are posted\. Check back after the first few events appear\.
• *Wrong date extracted?* Use /manage → ✏️ Edit → 📅 Date to correct it without re\-posting\.
• *Bot not responding?* You must verify first \(/verify in DM\) before any features work\.
• *Share with friends:* Tap 🔗 Share on any event card to send them a direct link\.
• *Posting from a group?* The bot needs to be added to the group as a member first\.
