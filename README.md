# Meet Pam, our party planner agent!

The holiday season coming up means plenty of events to host and attend. While this is all fun, there are so many things to think about when planning events - from finding a suitable time or place for hosting to having to put together decorations, music, and invitations that fit the theme. We wanted to create an agent that would help streamline this process and came up with Pam, the party planner.

You can tell her the occasion, city, date, party length and theme, and she can check the forecast for your date, and suggests backup dates if it looks bad, find food and cocktail recipes that match your theme, make a mood board of images for inspiration, and builds a playlist of real songs based on your specifications that you can preview right in the chat. She can also find you restaurants where you can host your event and create an invitation with your party details.


## Tools
Our agent has 7 tools in total: 

1. get_weater: gets the weather from OpenMeteo based on the city and date
2. check_party_date: gets the full 16 day forecast and checks the party day - in the case that the weather is bad, it lists the problems and offers up to 3 backup dates with good weather
3. find_recipes: uses TheMealDB and TheCocktailDB to find recipes for food and drinks, returning up to 6 recipes with names and links to the recipe page
4. make_mood_board: takes 1-3 searches and finds matching Are.na boards and takes image blocks from them, returning up to 9 images to make a mood board
5. make_party_playlist: searches iTunes for songs that covers the party's length up to 60 songs, returns song title, artist, year, 30 second preview, link, and artwork
6. find_restaurants: finds locates with Nominatim and uses Overpass for named restaurants, returning up to 8 restaurants with cuisine, distance, address, website, phone, hours, takeaway/delivery and a Google Maps link
7. make_invitation: takes the input title, date, time, and location, and creates an invitation with artwork - it also builds an "add to Google Calendar" link

## How to use Pam

You can try it out here: **https://pam-the-party-planner-git-704627147159.europe-west1.run.app** 

Type in the box at the bottom, or click one of the sample queries under the title to get started. Reload the page to start a new conversation. 

Note: The OpenMeteo API can only reach about 16 days ahead, so pick a date within that timeframe to see the forecast and backup-date tools in action.

## Team
Suvethika Kandasamy (sk5697) and Gabriella Chu (gc3203).
