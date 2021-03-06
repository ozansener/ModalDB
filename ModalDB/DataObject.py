'''
Class: DataObject
=================

Description:
------------
	
	Common ancestor of objects that store data both in-memory and 
	on disk. This is useful for applications in which there are components 
	that are both very large and very small (i.e. text, associated images)

	Key properties:
		- abstracts away details of what items are stored where
		- lazily loads items on disk

	Terminology:
		- item: key, value pair
		- mongo_doc: representation that appears in mongodb, containing 
					fast-access items 
		- root: path to directory containing slow-access items



Example Usage:
--------------
	
	data_object = DataObject(schema, mongo_dict, root)
	data_object.set_schema(schema)

##################
Jay Hack
Fall 2014
jhack@stanford.edu
##################
'''
import os
import dill as pickle
from copy import deepcopy

from ModalDicts import DiskDict, MemoryDict
from ChildContainer import ChildContainer


class DataObject(object):
	"""
		Example Usage:
		--------------

			# Create DataObject (should be subclassed...)
			data_object = DataObject(mongo_doc, schema)

			# Access items on disk and in memory identically
			disk_item = data_object[disk_item_name] # loads from disk
			mem_item = data_object[mem_item_name] # grabs from MongoDB

		mongo_doc:
		----------
		contains:
			- _id: self identifier 
			- root: path to this object's directory
			- items: metadata on contained items
			- children: mapping from child type to children

		children:
		---------
		children may be identified to their parent differently than they 
		are globally. For example, the frame '1' in a video 'myvid' is '1'
		its parent, while it's known as 'myvid/Frame/1' globally.


	"""
	def __init__(self, mongo_doc, schema, client):
		"""
			Args:
			-----
			- mongo_doc: dict containing root, in-memory items
			- schema: dict containing schema for this object
			- client: reference to ModalClient object
		"""
		self._id = mongo_doc['_id']
		self.root = mongo_doc['root']
		self.schema = schema
		self.client = client
		self.items = {
						'disk':DiskDict(mongo_doc, self.schema),
						'memory':MemoryDict(mongo_doc, self.schema)
					}
		self.children = ChildContainer(self._id, schema, mongo_doc)





	################################################################################
	####################[ ITEM ACCESS	]###########################################
	################################################################################

	def __contains__(self, key):
		return any([key in d for d in self.items.values()])


	def detect_keyerror(self, key):
		if not key in self:
			raise KeyError("No such item: %s" % key)


	def get_mode(self, key):
		return self.schema[key]['mode']


	def update_mongo_doc(self):
		"""
			updates the mongodb representation 
			of this DataObject 
		"""
		new_item_dict = {}
		for k in self.items['disk'].present_items:
			new_item_dict[k] = self.items['disk'].paths[k]
		for k in self.items['memory'].present_items:
			new_item_dict[k] = self.items['memory'].data[k]
		self.client.update_mongo_doc(type(self), self._id, new_item_dict)



	def __getitem__(self, key):
		self.detect_keyerror(key)
		return self.items[self.get_mode(key)][key]


	def __setitem__(self, key, value):
		self.detect_keyerror(key)
		if self.items[self.get_mode(key)][key] is None:	
			self.items[self.get_mode(key)][key] = value
			self.update_mongo_doc()
		else:
			self.items[self.get_mode(key)][key] = value


	def __delitem__(self, key):
		self.detect_keyerror(key)
		del self.items[self.get_mode(key)][key]
		self.update_mongo_doc()





	################################################################################
	####################[ ITEM METADATA ]###########################################
	################################################################################

	@property
	def present_items(self):
		"""
			returns set of names of items that are present
		"""
		return set.union(*[md.present_items for md in self.items.values()])

	@property
	def absent_items(self):
		"""
			returns set of names of items that are in schema 
			yet not present 
		"""
		return set.union(*[md.absent_items for md in self.items.values()])



	################################################################################
	####################[ CHILDREN	]###############################################
	################################################################################

	def get_child_dir(self, childtype):
		"""
			returns path to directory containing childtype
		"""
		assert self.children.is_valid_childtype(childtype)
		return os.path.join(self.root, childtype.__name__)
		

	def get_child(self, *args):
		"""
			Returns a child object; Must specify child's datatype if 
			there are multiple childtypes for this object.

			Args:
			-----
			- (Optional, first): childtype (can omit if there's only one)
			- raw id of child
		"""
		datatype, full_id = self.children.get(*args)
		return self.client.get(datatype, full_id)


	def get_random_child(self, datatype=None):
		"""
			Returns a child object; Must specify child's datatype if 
			there are multiple childtypes for this object.

			Args:
			-----
			- (Optional, first): childtype (can omit if there's only one)
		"""
		datatype, child_id = self.children.get_random(datatype)
		return self.get_child(datatype, child_id)


	def iter_children(self, childtype=None):
		for childtype, child_id in self.children.iter(childtype):
			yield self.get_child(childtype, child_id)


	def add_child(self, *args):
		"""
			Adds the record of the child to this dataobject's children.

			Args:
			-----
			- (Optional, first): childtype (can omit if there's only one)
			- id of child; can be either full or raw
		"""
		self.children.add(*args)
		self.client.get_collection(type(self)).update(
					{'_id':self._id}, 
					{'$set':{'children':self.children.childtype_dicts}},
					upsert=False
		)



	def delete_child(self, *args):
		"""
			Deletes the record of this child from this dataobject's 
			children.

			Args:
			-----
			- (Optional, first): childtype (can omit if there's only one)
			- id of child; can be either full or raw
		"""
		self.children.delete(*args)
		self.client.get_collection(type(self)).update(
					{'_id':self._id}, 
					{'$set':{'children':self.children.childtype_dicts}},
					upsert=False
		)


