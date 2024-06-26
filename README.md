## Intro
This is a quick script to create a pretix seating plan for beer benches typically used in germany.

## Usage
1. Change the configuration at the beginning of `seating.py` to suit your specific situation.
2. Run `python seating.py` to create your seating plan.
3. Import your seating plan to the [Pretix Seating Plan Web Editor](https://seats.pretix.eu) to refine it further.

## Motivation
On a "beer bench table", people who belong together typically sit opposite to each other. 

A "row" (one table) furthermore would span its seats into two physical rows, to make booking more comfortable.

To quickly solve these issues, I found it easier to write this script than to manually arrange seats.

## DevContainer support
If you do not have python installed, you can just run this code in a DevContainer or CodeSpace.
