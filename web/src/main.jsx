import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import Settings from "./pages/Settings/Settings";
import Poller from "./Poller";
import "./index.scss";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import { grey } from "@mui/material/colors";
import "./general.scss";

import { createHashRouter, RouterProvider, Navigate } from "react-router-dom";

export const router = createHashRouter([
    {
        path: "/",
        element: <Navigate to="/home" />,
        errorElement: <div>404</div>,
    },
    {
        path: "/home",
        element: <App selectedPage={0} />,
    },
    {
        path: "/player",
        element: <App selectedPage={1} />,
    },
    {
        path: "/browser",
        element: <App selectedPage={2} />,
    },
    {
        path: "/settings",
        // element: <App selectedPage={3} />,
        children: [
            {
                path: "/settings",
                element: <App selectedPage={3} />,
            },
            {
                path: "streams",
                element: <Settings openPage="streams" />,
            },
            {
                path: "zones",
                element: <Settings openPage="zones" />,
            },
            {
                path: "groups",
                element: <Settings openPage="groups" />,
            },
            {
                path: "sessions",
                element: <Settings openPage="sessions" />,
            },
            {
                path: "presets",
                element: <Settings openPage="presets" />,
            },
            {
                path: "config",
                element: <Settings openPage="config" />,
            },
            {
                path: "about",
                element: <Settings openPage="about" />,
            },
            // TODO: maybe redirect to update page. this is only accessable via URL
            // {
            //   path: 'updates',
            //   element: <Settings openPage="updates" />,
            // },
        ],
    },
    // {
    //   path: '/settings/streams',
    //   element: <div>Streams</div>,
    // }
]);

const darkTheme = createTheme({
    palette: {
        primary: {
            main: '#90caf9', // MUI default blue
            light: '#e3f2fd',
            dark: '#42a5f5',
            contrastText: '#fff',
          },
        mode: "dark",
        background: {
            paper: "#2a2a2a", // TODO: no good way of getting this from scss...
        },
    },
    typography: {
        fontFamily: "open sans"
    },
    components: {
        MuiCssBaseline: {
            styleOverrides: `
                @font-face {
                    font-family: 'open sans';
                    color: '#ffffff';
                }
            `,
        }
    }
});

ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
        <ThemeProvider theme={darkTheme}>
            <CssBaseline />
            <Poller>
                <RouterProvider router={router} />
            </Poller>
        </ThemeProvider>
    </React.StrictMode>
);
