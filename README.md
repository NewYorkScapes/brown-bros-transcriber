# brown-bros-transcriber

A proof-of-concept Flask app to handle transcriptions of segments and identifying token boundaries

Progress:

2 pages:
 - Home ('/'): loads a segment image by querying sqlite3 db file, **segments** table, in which filenames, and ID, and bbox coordinates are stored (for later use potentially to make a context image). Loads a form into which the user can type the transcription, stores a session variable indicating what ID has been selected. Crudely selects the segment based on the first available row in which the **complete** field is 0, meaning not yet transcribed. Sends transcription via http POST.
 
 - Addrec ('/addrec'): confirmation page that tells the user that the transcription has been added to the DB. Behind the scenes the page adds a new record to the **transcriptions** table using the session-set ID as an identifier (for later JOIN) and the string transcription. Updates the **segments** table to indicate that a record has been transcribed (**segments.complete** = 1).
 
To Do:

 - Handle potential DB locking or problem of concurrent writings to **segments** table.
 >> Status: Possibly now done by using a checkout field in the segments table so that when a user requests a record, the checkout is immediately set to "1", so that the next user cannot be assigned that record but rather the next available one. 
 - Fix crude method of identifying the next segment needing to be served?
 - Look at adding token boundary GUI
 >> Status: More or less ready to go. Main bug is that small segments will fail to show the full markup toolbox, which may be confusing to users.
 - Consider using bbox coordinates to generate contextual larger image to accompany segment
 - Work through management, if needed, of batch loading of segments and auto updating DBs to reflect new segments. Possibly deploy a batch loader script here
 - Decide on conventions for segment naming
 >> Status: Done. This is being done at point of segment generation
 - Build a export file builder that brings together all the information contained in SQL tables
 
Non-technical To Do:

 - Decide on conventions for transcribing things like fractions (1/2), etc.
 
 **How to Run**
 
 Clone repo, inside main directory run:
 
 <code>python app.py</code>
 
Open localhost
 