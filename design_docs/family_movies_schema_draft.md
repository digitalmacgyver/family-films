## Family Movie Project Collaboration Doc

## Version 1 schema proposal:

**digitial\_reels**

| Column | Data Type | Null / Not Null | Notes |
| :---- | :---- | :---- | :---- |
| id | string | NOT NULL | Primary Key \- Sting matching the label on the physical film canister |
| filename | string | NOT NULL | The filename of the media file that corresponds to this reel |
| format | string | NOT NULL | One of: 16mm, 8mm, Super-8, etc. |
| fps | int | NOT NULL | The frames per second this film is in |
| duration | int | NOT NULL | The number of frames |
| sound | bool | NOT NULL | Does this source have an audio signal |

**sequences**

| Column | Data Type | Null / Not Null | Notes |
| :---- | :---- | :---- | :---- |
| reel\_id | string | NOT NULL | Foreign Key to digital\_reels.id, first column in primary key of film sequences |
| sequence\_num | int | NOT NULL | The ordinal number of this sequence on reel\_id, e.g. 1 for the first sequence, etc., the second column in the primary key of film sequences |
| title | string | NOT NULL | A short title of this sequence, such as could be shown on a generated title card, e.g. “Christmas 2023” |
| description | string | NOT NULL | A short (a few paragraphs at most) description of the sequence. (Defaults to the empty string) |
| start\_frame | int | NOT NULL | The first frame of the sequence |
| duration | int | NOT NULL | The number of frames in this sequence (e.g. if start frame is 5 and duration is 3, the sequence consists of frames 5, 6, and 7). |
| intro\_text | string | NOT NULL | Introductory text for the scene, it could be narrated over a title card, or rendered on screen as text. (Defaults to the empty string) |

**people**

| Column | Data Type | Null / Not Null | Notes |
| :---- | :---- | :---- | :---- |
| id | int | NOT NULL | An arbitrary unique integer for this person, the primary key for the people table |
| fname | string | NOT NULL | First name |
| lname | string | NOT NULL | Last name |
| birth\_date | date | NULL |  |
| father\_id | int | NULL | Optional FK to this table indicating the parents of this person |
| mother\_id | int | NULL | Optional FK to this table indicating the parents of this person |
| spouse\_id | int | NULL | Optional FK to this table indicating the spouse of this person |
| notes | string | NULL | Any notes about this person. (Defaults to the empty string) |

**sequence\_people**

| Column | Data Type | Null / Not Null | Notes |
| :---- | :---- | :---- | :---- |
| reel\_id | string | NOT NULL | Foreign Key to sequences |
| sequence\_num | int | NOT NULL | Foreign Key to sequences |
| person\_id | int | NOT NULL | Foreign key to people |

**locations**

| Column | Data Type | Null / Not Null | Notes |
| :---- | :---- | :---- | :---- |
| id | int | NOT NULL | An arbitrary unique integer for this location, the primary key for the people table |
| name | string | NOT NULL | The name of this location |
| description | string | NOT NULL | A longer description of this location. (Defaults to the empty string.) |
| geo\_coordinates | TBD | NULL | Optional geographical coordinates for this location, the data type depends on the database, some have native geo types, otherwise we can store lat/long as floats. |

**sequence\_locations**

| Column | Data Type | Null / Not Null | Notes |
| :---- | :---- | :---- | :---- |
| reel\_id | string | NOT NULL | Foreign Key to sequences |
| sequence\_num | int | NOT NULL | Foreign Key to sequences |
| location\_id | int | NOT NULL | Foreign key to locations |
| is\_primary | bool | NOT NULL | Is this the primary location for this sequence? The idea is a sequence will have at most one is\_primary location, which can be shown on a title card (Defaults to FALSE.) |

**tags**

| Column | Data Type | Null / Not Null | Notes |
| :---- | :---- | :---- | :---- |
| tag | string | NOT NULL | A short tag indicating some element of the film, e.g. “holidays” or “nature” or “pets.” Primary key |

**sequence\_tags**

| Column | Data Type | Null / Not Null | Notes |
| :---- | :---- | :---- | :---- |
| reel\_id | string | NOT NULL | Foreign Key to sequences |
| sequence\_num | int | NOT NULL | Foreign Key to sequences |
| tag | string | NOT NULL | Foreign Key to tags |
| is\_auto | bool | NOT NULL | Was this tag applied automatically by machine vision or some other technique. (Defaults to false.) |

## Schema Notes:

The proposed schema is suitable for describing an inventory of the raw video we have, and some metadata of interest on various sequences.

Eventually we’d refine these sequences into more finished video projects, for example combining parts of multiple sequences into a supercut of “holidays” or “kids playing.” This might also involve editorial changes like adding information cards to the video at points, and changing elements of the raw video for presentation like frame rate adjustments for other players, reduced resolution for manageable sizes, etc.

* This schema doesn’t yet have the tables needed to describe derived videos of the raw sources. (Maybe it never will need that)

Advanced ideas considered and not implemented:

* We could try to tag the presence of various people at a high degree of fidelity, e.g. have a person\_presence table which has a record each time a person appears within a sequence, listing the start and end frames of that appearance. That would make it possible in theory to automate things like “A video with all the time that John Hayward Sr. is on screen”  
* A “sequence” here is defined by the human editor as a contiguous piece of one of our raw film reels that is of interest. Usually all the shots in a sequence will be common to a given time, location, or event.  
  * A sequence is made of one or more “shots” \- which is one take from the camera.  
  * We could have identified “shots” in our inventory, but we have hundreds if not thousands of shots. Sequences seems more manageable.  
    * It is plausible with machine vision / automation to automatically detect shots within a segment and note their start and end times

