# AmpliPi WebApp version 2
### hi. 

index.html is the entry point. It first checks if the nullish operator works then passes control to /src/main.jsx.

main.jsx handles page routing, MUI theme, and wraps the whole app in a "Poller" component which launches an interval that polls status from amplipi and displays the LoadingPage while state is still null or when we are unable to poll state from amplipi.

App.jsx holds onto state via useStatusStore, which contains the status dict, and usePersistentStore, which keeps track of which player is selected so that the app will resume to the previously selected player. 