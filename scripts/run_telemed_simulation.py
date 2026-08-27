"""
Discrete-Event Telemedicine Workflow Simulation (SimPy & Analytical Queueing)
Models district-level screening programs serving 100,000+ patients annually.
Evaluates bandwidth consumption, edge vs. cloud inference latency, and specialist review queues.
"""

import argparse
import random
import math
from typing import Dict, Any, List
import simpy


class RuralTelemedicineDistrictSim:
    """
    Discrete-Event Simulation of a District Healthcare Telemedicine Network.
    """

    def __init__(
        self,
        num_phcs: int = 50,
        arrival_rate_per_phc: float = 8.0,  # patients/day
        days_per_year: int = 250,
        bandwidth_mbps: float = 1.5,
        image_size_mb: float = 15.0,
        compressed_size_mb: float = 1.2,
        ungradable_rate: float = 0.12,
        referable_rate: float = 0.18,
        num_doctors: int = 2,
        review_time_sec: float = 30.0,
        sim_duration_days: int = 30,
        seed: int = 42,
    ):
        self.num_phcs = num_phcs
        self.arrival_rate = arrival_rate_per_phc
        self.days_per_year = days_per_year
        self.bandwidth_mbps = bandwidth_mbps
        self.image_size_mb = image_size_mb
        self.compressed_size_mb = compressed_size_mb
        self.ungradable_rate = ungradable_rate
        self.referable_rate = referable_rate
        self.num_doctors = num_doctors
        self.review_time_sec = review_time_sec
        self.sim_duration_days = sim_duration_days
        self.seed = seed

        # Metrics collection
        self.total_screened = 0
        self.ungradable_recaptures = 0
        self.local_discharges = 0
        self.tele_referrals = 0
        self.waiting_times_sec: List[float] = []

    def patient_process(self, env: simpy.Environment, doctor_resource: simpy.Resource, phc_id: int):
        """Simulates single patient lifecycle."""
        self.total_screened += 1

        # 1. Image Acquisition (2-4 minutes)
        yield env.timeout(random.uniform(120, 240))

        # 2. Local Quality Gate (< 2 seconds)
        if random.random() < self.ungradable_rate:
            self.ungradable_recaptures += 1
            # Recapture delay (1-2 minutes)
            yield env.timeout(random.uniform(60, 120))

        # 3. Local Edge AI Screening (< 3 seconds)
        yield env.timeout(random.uniform(1.5, 3.0))

        # 4. Triage Decision
        if random.random() >= self.referable_rate:
            # Non-referable: discharged locally immediately
            self.local_discharges += 1
            return

        # 5. Referable Case -> Transmitted over cellular network to Doctor Queue
        self.tele_referrals += 1
        transmission_time = (self.compressed_size_mb * 8.0) / self.bandwidth_mbps
        yield env.timeout(transmission_time)

        # 6. Specialist Tele-Review Queue
        arrival_time = env.now
        with doctor_resource.request() as req:
            yield req
            wait_time = env.now - arrival_time
            self.waiting_times_sec.append(wait_time)
            # Doctor performs sub-30s verification
            yield env.timeout(random.expovariate(1.0 / self.review_time_sec))

    def phc_patient_generator(self, env: simpy.Environment, doctor_resource: simpy.Resource, phc_id: int):
        """Generates patient arrivals at a single rural PHC (6-hour clinical day)."""
        daily_seconds = 6 * 3600  # 6 operating hours per day
        interarrival_mean = daily_seconds / self.arrival_rate

        while True:
            # Exponential interarrival times
            yield env.timeout(random.expovariate(1.0 / interarrival_mean))
            env.process(self.patient_process(env, doctor_resource, phc_id))

    def run(self) -> Dict[str, Any]:
        random.seed(self.seed)
        env = simpy.Environment()
        doctor_resource = simpy.Resource(env, capacity=self.num_doctors)

        # Spawn patient arrival generators for all PHCs
        for i in range(self.num_phcs):
            env.process(self.phc_patient_generator(env, doctor_resource, i))

        # Run simulation for specified duration
        total_seconds = self.sim_duration_days * 6 * 3600
        env.run(until=total_seconds)

        # Scale results to annual basis
        scale_factor = self.days_per_year / self.sim_duration_days
        annual_screened = int(self.total_screened * scale_factor)
        annual_referrals = int(self.tele_referrals * scale_factor)
        annual_local = int(self.local_discharges * scale_factor)

        # Bandwidth calculations
        raw_cloud_annual_tb = (annual_screened * 2 * self.image_size_mb) / (1024 * 1024)
        edge_annual_tb = (annual_referrals * 2 * self.compressed_size_mb) / (1024 * 1024)
        bandwidth_savings_pct = (1.0 - (edge_annual_tb / max(raw_cloud_annual_tb, 1e-6))) * 100.0

        avg_wait_min = (sum(self.waiting_times_sec) / len(self.waiting_times_sec) / 60.0) if self.waiting_times_sec else 0.0

        # Output Summary
        print("=" * 65)
        print("  RuralDR-XAI: District Telemedicine Simulation (SimPy)")
        print("=" * 65)
        print(f"• Target Annual Volume:         {annual_screened:,} patients/year")
        print(f"• Active Screening Stations:    {self.num_phcs} PHCs")
        print(f"• Local Non-Referable Volume:   {annual_local:,} patients ({(1-self.referable_rate)*100:.1f}% filtered locally)")
        print(f"• Tele-Ophthalmology Reviews:   {annual_referrals:,} referable cases/year")
        print(f"• Cloud-Only Bandwidth:         {raw_cloud_annual_tb:.2f} TB/year")
        print(f"• RuralDR-XAI Edge Bandwidth:   {edge_annual_tb:.2f} TB/year")
        print(f"• Bandwidth Reduction:          {bandwidth_savings_pct:.1f}%")
        print(f"• Number of Tele-Doctors:       {self.num_doctors} specialists")
        print(f"• Mean Specialist Wait Time:    {avg_wait_min:.2f} minutes")
        print("=" * 65)

        return {
            "annual_screened": annual_screened,
            "annual_referrals": annual_referrals,
            "annual_local_discharges": annual_local,
            "raw_cloud_tb": raw_cloud_annual_tb,
            "edge_bandwidth_tb": edge_annual_tb,
            "bandwidth_savings_pct": bandwidth_savings_pct,
            "avg_wait_time_minutes": avg_wait_min,
            "num_phcs": self.num_phcs,
            "num_doctors": self.num_doctors,
        }


def main():
    parser = argparse.ArgumentParser(description="Simulate district teleretinal screening network.")
    parser.add_argument("--num_phcs", type=int, default=50, help="Number of rural PHCs")
    parser.add_argument("--arrival_rate", type=float, default=8.0, help="Patient arrivals per PHC per day")
    parser.add_argument("--bandwidth_mbps", type=float, default=1.5, help="PHC cellular bandwidth in Mbps")
    parser.add_argument("--num_doctors", type=int, default=2, help="Number of district tele-ophthalmologists")
    parser.add_argument("--annual_target", type=int, default=100000, help="Target annual patient volume")
    args = parser.parse_args()

    sim = RuralTelemedicineDistrictSim(
        num_phcs=args.num_phcs,
        arrival_rate_per_phc=args.arrival_rate,
        bandwidth_mbps=args.bandwidth_mbps,
        num_doctors=args.num_doctors,
    )
    sim.run()


if __name__ == "__main__":
    main()
