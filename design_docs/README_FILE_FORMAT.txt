The .xls files in this directory contain some rows of front matter metadata, followed by tabular output.

The tabular output will always contain some leading columns, and then
files may differ for the trailing columns.

To interpret the "Haywards Present" column, typically located in column F of the sheet, it is a string of 1's and 0's where each 1 indicates the presence of a particular person - analagous to a bitfield.

If the first digit is 1 then John Hayward Sr. is present in this segment.
If the second digit is 1 then Josephine Hayward is present in this segment.
If the third digit is 1 then John Hayward Jr. is present in this segment.
If the fourth digit is 1 then Joy Hayward is present in this segment.
If the fifth digit is 1 then Mark Hayward is present in this segment.
If the sixth digit is 1 then Ruth Hayward is present in this segment.
If the seventh digit is 1 then James Hayward is present in this segment.

The format of the "Start" and "End" columns located in column A and B
is the relevant time in text: HH:MM:SS:FF format where HH is hours+1,
MM is minutes, SS is seconds, and FF is frame number. These cells also
contain a thumbnail image of the corresponding frame.

The optional "16fps Start Seconds" column includes the actual time
when the final videos are rendered that this segment will begin. The
mandatory Start and End columns include the start and end time of this
film segment offset by +1 hour under the assumption that the film is
played back at 29.97 frames per second, which is incorrect.

Throughout these files when a column has a case insensitive value of:
"u" or "unknown" it indicates the information is the special "unknown" value.


