## Usage
+. go to the confluence page you record acceptance criteria
+. select 'page information' under this tag '...', you will see the page id in url
+. run python srcipt with command: python ac_transer_from_confluence_to_testlink.py pageid     

Phase I:

1. confluence with story and ac, create a new folder in testlink to store those ac transfered cases
2. run script like transfer.py <page_id> <folder_id>, then cases transfer complete and ret map inserted in the confluence passed