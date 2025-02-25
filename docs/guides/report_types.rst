Understanding report types
##########################

Overview
========

Report types define what can be provided in a request. analytix automatically selects the most appropriate report type based on the dimensions, filters, and metrics you provide, so it is probably easier to think of report types as a single standard for validating requests.

Each report type has a set of valid:

* Dimensions
* Filters
* Metrics
* Sort options (usually the same as the valid metrics)

After a report type is selected by analytix, the provided attributes are compared against the valid ones for that report type, and errors are thrown on mismatches. For example, if "day" and "country" (two incompatible dimensions) are both provided, analytix will select the "Geography-based activity" report type (as the "country" dimension is checked before the "day" dimension), and the "day" dimension will be flagged as invalid.

Some report types are stricter that others; they also have:

* Their own set of valid sort options, separate to the set of valid metrics
* A maximum number of results

These report types are referred to internally as "detailed report types". Oftentimes, they are also far more picky about what filters can be provided and the values that can be passed to them.

In total, there are 43 report types -- 33 normal and 10 detailed.

List of report types
====================

Video reports
-------------

* Basic user activity
* Basic user activity (US)
* Time-based activity
* Time-based activity (US)
* Geography-based activity
* Geography-based activity (US)
* User activity by subscribed status
* User activity by subscribed status (US)
* Time-based playback details (live)
* Time-based playback details (view percentage)
* Geography-based playback details (live)
* Geography-based playback details (view percentage)
* Geography-based playback details (live, US)
* Geography-based playback details (view percentage, US)
* Playback locations
* Playback locations (detailed) [#f1]_
* Traffic sources
* Traffic sources (detailed) [#f1]_
* Device types
* Operating systems
* Device types and operating systems
* Viewer demographics
* Engagement and content sharing
* Audience retention
* Top videos by region [#f1]_
* Top videos by state [#f1]_
* Top videos by subscription status [#f1]_
* Top videos by YouTube product [#f1]_
* Top videos by playback detail [#f1]_

Playlist reports
----------------

* Basic user activity for playlists
* Time-based activity for playlists
* Geography-based activity for playlists
* Geography-based activity for playlists (US)
* Playback locations for playlists
* Playback locations for playlists (detailed) [#f1]_
* Top sources for playlists
* Top sources for playlists (detailed) [#f1]_
* Device types for playlists
* Operating systems for playlists
* Device types and operating systems for playlists
* Viewer demographics for playlists
* Top playlists [#f1]_

Ad performance reports
----------------------

* Ad performance

.. [#f1] Detailed report type

For more information about each report type, look at the `official documentation <https://developers.google.com/youtube/analytics/channel_reports#video-reports>`_ or the `source code <https://github.com/parafoxia/analytix/blob/main/analytix/report_types.py>`_.
