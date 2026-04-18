import { mount } from "svelte";
import App from "./App.svelte";
import "./app.css";
import "maplibre-gl/dist/maplibre-gl.css";

mount(App, { target: document.getElementById("app") });
