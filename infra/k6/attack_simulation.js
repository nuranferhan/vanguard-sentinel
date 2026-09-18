import http from "k6/http";
import { sleep } from "k6";

export const options = {
  scenarios: {
    burst_attack: {
      executor: "constant-arrival-rate",
      rate: 500,
      timeUnit: "1s",
      duration: "20s",
      preAllocatedVUs: 100,
      maxVUs: 300,
    },
  },
};

const GATEWAY_URL = "http://localhost:8000/gateway/player/action";
const TOKEN = __ENV.VANGUARD_TOKEN || "";

export default function () {
  const payload = JSON.stringify({ action: "move", x: 0, y: 0 });
  http.post(GATEWAY_URL, payload, {
    headers: { "Content-Type": "application/json", "X-Session-Token": TOKEN },
  });
  sleep(0.01);
}
