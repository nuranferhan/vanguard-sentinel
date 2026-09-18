import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "30s", target: 50 },
    { duration: "1m", target: 200 },
    { duration: "30s", target: 500 },
    { duration: "30s", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<300"],
    http_req_failed: ["rate<0.05"],
  },
};

const GATEWAY_URL = "http://localhost:8000/gateway/player/action";
const TOKEN = __ENV.VANGUARD_TOKEN || "";

export default function () {
  const payload = JSON.stringify({ action: "move", x: Math.random() * 100, y: Math.random() * 100 });
  const params = {
    headers: {
      "Content-Type": "application/json",
      "X-Session-Token": TOKEN,
    },
  };

  const response = http.post(GATEWAY_URL, payload, params);

  check(response, {
    "status is 200 or 429": (r) => r.status === 200 || r.status === 429,
  });

  sleep(0.2);
}
