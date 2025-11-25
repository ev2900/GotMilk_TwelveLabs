# GotMilk? TwelveLabs

<img width="275" alt="map-user" src="https://img.shields.io/badge/cloudformation template deployments-000-blue"> <img width="85" alt="map-user" src="https://img.shields.io/badge/views-000-green"> <img width="125" alt="map-user" src="https://img.shields.io/badge/unique visits-011-green">

# Overview

I wanted to explore [TwelveLabs](https://www.twelvelabs.io/) capabilities to work with videos. 

I built a solution that solves a fictitious scenario. The scenario:
* A Brand Partnership division is partnering with a brand to re-create a modern version of the iconic got milk? Campaign.
* The team wants to ability to validate if social media posts (.mp4 files) are actually part of their campaign.
* If the social media posts are part of the campaign they want to be able to group posts / understand similiarities on a variety of topics ex. activity, location etc.

# Architecture



# Deploying the Solution on AWS

Click the button below to deploy the [gotmilk_twelvelabs.yaml](https://github.com/ev2900/GotMilk_TwelveLabs/blob/main/gotmilk_twelvelabs.yaml) CloudFormation. This will deploy all of the components pictured in the architecture.

> [!WARNING]
> The CloudFormation stack creates IAM role(s) that have ADMIN permissions. This is not appropriate for production deployments. Scope these roles down before using this CloudFormation in productio

[![Launch CloudFormation Stack](https://sharkech-public.s3.amazonaws.com/misc-public/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home#/stacks/new?stackName=gotmilk-twelvelabs&templateURL=https://sharkech-public.s3.amazonaws.com/misc-public/gotmilk_twelvelabs.yaml)


