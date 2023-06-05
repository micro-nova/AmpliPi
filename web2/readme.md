# AmpliPi WebApp Version 2

## Architecture
index.html is the entry point. It first checks if the nullish operator works then loads /src/main.jsx.

main.jsx handles page routing, MUI themeing, and wraps the whole app in the "Poller" component which launches an interval that polls status from amplipi and displays the LoadingPage while state is still null or when we are unable to poll state from amplipi.

App.jsx holds onto state via useStatusStore, which contains the status dict from amplipi, and usePersistentStore, which keeps track of which player is selected so that the app will resume to the previously selected player on page reload. App.jsx also displays the selected page along with the MenuBar for changing the selected page.

In the current version, the MenuBar can naviate to three pages: Home, Player, Settings.

The Player page is only accessable when a player is selected on the home page.


