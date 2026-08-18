import type { NextConfig } from "next";

/* Excel motoru ayrı bir Python (FastAPI) sürecinde çalışır. İstekleri Next
   üzerinden yönlendiriyoruz: böylece tarayıcı tek origin görür, CORS ayarı
   gerekmez ve dağıtımda adres tek yerden değişir. */
const MOTOR = process.env.MOTOR_ADRESI ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:yol*", destination: `${MOTOR}/api/:yol*` }];
  },
};

export default nextConfig;
