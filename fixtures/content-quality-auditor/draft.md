# How to Set Up a Home Network for Remote Work

Working from home means your router is now office infrastructure. This guide walks through setting up a home network that keeps video calls stable and work devices separate from the family TV. It covers consumer routers and mesh systems; it does not cover enterprise VLAN design or ISP-side configuration.

## Who this is for

This guide is for remote employees and freelancers who have a standard ISP router and want fewer dropped calls. You do not need networking experience.

## Key takeaways

- Put work devices on a separate Wi-Fi network (a guest network works) so a smart TV update cannot stall your meeting.
- Use the 5 GHz band for your laptop and reserve 2.4 GHz for low-bandwidth devices.
- A wired connection to the router removes most call drops; a 15 m Cat6 cable costs about $12.
- Set Quality of Service (QoS) to prioritize your work laptop when the router supports it.

## Step 1: Measure what you have

Run a speed test at your desk on Wi-Fi and again with a cable. Write both numbers down. In our own test the desk Wi-Fi result was 48 Mbps down and 9 Mbps up, while the cabled result was 310 Mbps down and 20 Mbps up. Video calls need roughly 3 Mbps up per participant stream, so the upload number matters more than the download number.

## Step 2: Separate work from everything else

Most routers made after 2018 offer a guest network. Enable it, give it a distinct name such as "Home-Work", and move the work laptop, dock and printer onto it. Keep the TV, consoles and smart speakers on the main network. Guest networks usually block device-to-device traffic, which also means a compromised smart plug cannot reach your laptop.

## Step 3: Pick the right band

Connect the laptop to the 5 GHz network. It is faster but has shorter range; if your desk is two walls away from the router, a mesh node or a cable will beat any band choice. Devices that only send small amounts of data (thermostats, bulbs) belong on 2.4 GHz.

## Step 4: Run a cable if you can

A cable removes interference entirely. Flat Cat6 cables run under carpet edges and door frames. If a cable is impossible, place a mesh node halfway between the router and the desk, not next to the desk.

## Step 5: Turn on QoS

Look for "QoS", "Traffic prioritization" or "Device priority" in the router admin page. Add the work laptop as the top-priority device. On routers without QoS, the guest-network split from Step 2 already prevents most contention.

## Problems we hit

- The ISP router reset its guest network after a firmware update, so devices silently rejoined the main network. Fix: check the network name after any update.
- A USB 3 hub next to the laptop interfered with 2.4 GHz. Moving the hub 30 cm away fixed it.

## When this does not apply

If you share a flat with three other remote workers, a consumer router will struggle regardless of settings; look at a small business access point. If your calls drop even on a cable, the problem is upstream at the ISP, and no home setting fixes that.

## Conclusion

Measure first, split work from home traffic, prefer 5 GHz or a cable, and turn on QoS. Those four changes fixed the dropped calls in our setup within an afternoon. Next, test your setup with a 30-minute call and compare against the numbers from Step 1.

## FAQ

**Do I need a new router?** Only if yours predates 2018 or has no guest network option.

**Does a mesh system replace a cable?** No. Mesh improves coverage; a cable removes interference.

**Is a guest network secure enough for work?** For most employers yes, because it isolates devices. Check your company's policy if you handle regulated data.
