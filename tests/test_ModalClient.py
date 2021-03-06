"""
Test: ModalClient
=================

Description:
------------
	
	Puts ModalClient through tests involving:
		- loading and saving schemas
		- inserting data objects



##################
Jay Hack
Fall 2014
jhack@stanford.edu
##################
"""
import os
import shutil
import dill as pickle
import unittest 
from copy import copy, deepcopy
import nose
from nose.tools import *
import numpy as np
from scipy.io import loadmat, savemat
from scipy.misc import imsave, imread

from ModalDB import *

from schema_example import schema_ex
from dataobject_example import video_data, frame_data, data_dir

class Test_ModalSchema(unittest.TestCase):

	################################################################################
	####################[ setUp	]###################################################
	################################################################################

	thumbnail_backup_path = os.path.join(data_dir, 'thumbnail.backup.png')
	thumbnail_path = os.path.join(data_dir, 'thumbnail.png')
	image_backup_path = os.path.join(data_dir, 'image.backup.png')
	image_path = os.path.join(data_dir, 'image.png')
	schema_path = os.path.join(data_dir, '.ModalDB_schema.pkl')


	def reset_images(self):
		shutil.copy(self.thumbnail_backup_path, self.thumbnail_path)
		shutil.copy(self.image_backup_path, self.image_path)

	def reset_filesystem(self):
		shutil.rmtree(os.path.join(data_dir, 'Video'))

	def reset(self):
		self.reset_images()
		self.reset_filesystem()

	def setUp(self):

		self.schema = ModalSchema(schema_ex)
		self.video_data = video_data
		self.frame_data = frame_data
		self.schema.save(self.schema_path)
		self.reset_images()


	def tearDown(self):
		pass






	################################################################################
	####################[ CREATION	]###############################################
	################################################################################

	def test_creation_1(self):
		"""
			BASIC CREATION PASSING IN SCHEMA
			--------------------------------
			merely constructs a ModalClient, loading the schema
		"""
		client = ModalClient(root=data_dir, schema=self.schema)


	def test_creation_2(self):
		"""
			BASIC CREATION LOADING DEFAULT SCHEMA
			-------------------------------------
			merely constructs a ModalClient, loading the schema
		"""
		client = ModalClient(root=data_dir)
		schema = client.schema
		self.assertTrue('filename' in schema[Frame]['image']) 
		self.assertTrue(schema[Frame]['image']['filename'] == 'image.png')
		self.assertTrue(not 'filename' in schema[Video]['summary'])





	################################################################################
	####################[ DATA INSERTION/DELETION	]###############################
	################################################################################

	def test_clear_db(self):
		"""
			BASIC INSERTION OF VIDEO AND FRAME (CP)
			---------------------------------------
			constructs a video and a frame, inserts them via CP 
		"""
		client = ModalClient(root=data_dir)
		client.clear_db()


	def test_insertion_cp(self):
		"""
			BASIC INSERTION OF VIDEO AND FRAME (CP)
			---------------------------------------
			constructs a video and a frame, inserts them via CP 
		"""
		self.reset()
		client = ModalClient(root=data_dir)
		client.clear_db()
		video = client.insert(Video, 'test_video', self.video_data, method='cp')
		frame = client.insert(Frame, 'test_frame', self.frame_data, parent=video, method='cp')

		self.assertEqual(type(video), Video)
		self.assertEqual(type(frame), Frame)

		self.assertTrue(os.path.exists(os.path.join(data_dir, 'Video/test_video/Frame/test_frame/image.png')))
		self.assertTrue(os.path.exists(os.path.join(data_dir, 'Video/test_video/thumbnail.png')))

		self.assertEqual(video['summary'], 'hello, world!')
		self.assertEqual(frame['subtitles'], 'hello, world!')
		self.assertEqual(video['thumbnail'].shape, (512, 512, 3))
		self.assertEqual(frame['image'].shape, (512, 512, 3))


	def test_insertion_mv(self):
		"""
			BASIC INSERTION OF VIDEO AND FRAME (MV)
			---------------------------------------
			constructs a video and a frame, inserts them via MV
		"""
		self.reset()
		client = ModalClient(root=data_dir)
		client.clear_db()
		video = client.insert(Video, 'test_video', self.video_data, method='mv')
		frame = client.insert(Frame, 'test_frame', self.frame_data, parent=video, method='mv')

		self.assertEqual(type(video), Video)
		self.assertEqual(type(frame), Frame)

		self.assertTrue(os.path.exists(os.path.join(data_dir, 'Video/test_video/Frame/test_frame/image.png')))
		self.assertTrue(os.path.exists(os.path.join(data_dir, 'Video/test_video/thumbnail.png')))

		self.assertEqual(video['summary'], 'hello, world!')
		self.assertEqual(frame['subtitles'], 'hello, world!')
		self.assertEqual(frame._id, 'test_video/test_frame')
		self.assertEqual(video['thumbnail'].shape, (512, 512, 3))
		self.assertEqual(frame['image'].shape, (512, 512, 3))


	def test_deletion(self):
		"""
			BASIC DELETION OF FRAME AND VIDEO 
			---------------------------------
			constructs a video and a frame, deletes them 
		"""
		self.reset()
		client = ModalClient(root=data_dir)
		client.clear_db()
		video = client.insert(Video, 'test_video', self.video_data, method='mv')
		frame = client.insert(Frame, 'test_frame', self.frame_data, parent=video, method='mv')

		client.delete(Frame, 'test_frame', parent=video)
		self.assertFalse(os.path.exists(os.path.join(data_dir, 'Video/test_video/Frame/test_frame')))

		client.delete(Video, 'test_video')
		self.assertFalse(os.path.exists(os.path.join(data_dir, 'Video/test_video/')))



	def test_get_basic(self):
		"""
			BASIC RETRIEVAL OF INSERTED FRAME AND VIDEO
			-------------------------------------------
			constructs a video and a frame, inserts them via mv, then
			retrieves them
		"""
		self.reset()
		client = ModalClient(root=data_dir)
		client.clear_db()
		video = client.insert(Video, 'test_video', self.video_data, method='mv')
		frame = client.insert(Frame, 'test_frame', self.frame_data, parent=video, method='mv')

		video = client.get(Video, 'test_video')
		frame = client.get(Frame, 'test_video/test_frame')

		self.assertEqual(video['summary'], 'hello, world!')
		self.assertEqual(frame['subtitles'], 'hello, world!')
		self.assertEqual(frame._id, 'test_video/test_frame')
		self.assertEqual(video['thumbnail'].shape, (512, 512, 3))
		self.assertEqual(frame['image'].shape, (512, 512, 3))

	def test_get_random(self):
		"""
			BASIC RANDOM RETRIEVAL OF INSERTED FRAME AND VIDEO
			--------------------------------------------------
			constructs a video and a frame, inserts them via mv, then
			retrieves them
		"""
		self.reset()
		client = ModalClient(root=data_dir)
		client.clear_db()
		video = client.insert(Video, 'video_1', self.video_data, method='cp')		
		client.insert(Frame, 'frame_1', self.frame_data, parent=video, method='cp')
		client.insert(Frame, 'frame_2', self.frame_data, parent=video, method='cp')
		client.insert(Frame, 'frame_3', self.frame_data, parent=video, method='cp')

		frame = client.get_random(Frame)
		self.assertEqual(frame['image'].shape, (512, 512, 3))



	def test_get_child(self):
		"""
			BASIC RETRIEVAL OF CHILD OF VIDEO
			---------------------------------
			constructs a video and a frame, inserts them via mv, then
			retrieves them
		"""
		self.reset()
		client = ModalClient(root=data_dir)
		client.clear_db()
		video = client.insert(Video, 'video_1', self.video_data, method='cp')
		client.insert(Frame, 'frame_1', self.frame_data, parent=video, method='cp')
		client.insert(Frame, 'frame_2', self.frame_data, parent=video, method='cp')
		client.insert(Frame, 'frame_3', self.frame_data, parent=video, method='cp')

		video = client.get(Video, 'video_1')

		frame1 = video.get_child(Frame, 'frame_1')
		frame2 = video.get_child(Frame, 'frame_2')
		frame3 = video.get_child(Frame, 'frame_3')

		self.assertEqual(frame3['subtitles'], 'hello, world!')
		self.assertEqual(frame3['image'].shape, (512, 512, 3))
		self.assertEqual(frame3._id, 'video_1/frame_3')


	def test_iter_children(self):
		"""
			ModalClient: ITERATION THROUGH DATAOBJECT CHILDREN
			--------------------------------------------------
			constructs a video and a frame, inserts them via mv, then
			retrieves them
		"""
		self.reset()
		client = ModalClient(root=data_dir)
		client.clear_db()
		video = client.insert(Video, 'video_1', self.video_data, method='cp')
		client.insert(Frame, 'frame_1', self.frame_data, parent=video, method='cp')
		client.insert(Frame, 'frame_2', self.frame_data, parent=video, method='cp')
		client.insert(Frame, 'frame_3', self.frame_data, parent=video, method='cp')

		video = client.get(Video, 'video_1')
		for frame in video.iter_children(Frame):
			self.assertEqual(frame['image'].shape, (512, 512, 3))


	def test_get_random_child(self):
		"""
			ModalClient: RANDOM ACCESS TO DATAOBJECT CHILDREN
			-------------------------------------------------
			iterates through all frames 
		"""
		self.reset()
		client = ModalClient(root=data_dir)
		client.clear_db()
		video = client.insert(Video, 'video_1', self.video_data, method='cp')
		client.insert(Frame, 'frame_1', self.frame_data, parent=video, method='cp')
		client.insert(Frame, 'frame_2', self.frame_data, parent=video, method='cp')
		client.insert(Frame, 'frame_3', self.frame_data, parent=video, method='cp')

		frame1 = video.get_random_child()
		frame2 = video.get_random_child(Frame)
		self.assertEqual(frame1['image'].shape, (512, 512, 3))
		self.assertEqual(frame2['image'].shape, (512, 512, 3))	


	def test_iter(self):
		"""
			ModalClient: ITERATION THROUGH FRAMES
			-------------------------------------
			iterates through all frames 
		"""
		self.reset()
		client = ModalClient(root=data_dir)
		client.clear_db()
		video = client.insert(Video, 'video_1', self.video_data, method='cp')
		client.insert(Frame, 'frame_1', self.frame_data, parent=video, method='cp')
		client.insert(Frame, 'frame_2', self.frame_data, parent=video, method='cp')
		client.insert(Frame, 'frame_3', self.frame_data, parent=video, method='cp')

		for frame in client.iter(Frame):
			self.assertEqual(frame['image'].shape, (512, 512, 3))



	################################################################################
	####################[ ADDING/REMOVING ITEMS	]###################################
	################################################################################

	def test_add_item(self):
		"""
			ModalClient: ADDING ITEMS
			-------------------------
			adds an item to the schema and tries to set it 
		"""
		self.reset()
		client = ModalClient(root=data_dir)
		client.clear_db()
		video = client.insert(Video, 'video_1', self.video_data, method='cp')
		client.insert(Frame, 'frame_1', self.frame_data, parent=video, method='cp')
		client.insert(Frame, 'frame_2', self.frame_data, parent=video, method='cp')
		client.insert(Frame, 'frame_3', self.frame_data, parent=video, method='cp')

		#=====[ Add an item for frames 	]=====
		client.add_item(Frame, 'skeleton', {	
											'mode':'disk',
											'filename':'skeleton.pkl',
											'load_func':lambda p: pickle.load(open(p,'r')),
											'save_func':lambda x, p: pickle.dump(x, open(p, 'w'))
											})

		#=====[ Set this item for a few frames	]=====
		skel = '... NOT ACTUALLY A SKELETON ...'
		frame = video.get_child('frame_1')
		frame['skeleton'] = skel

		#=====[ make sure it holds	]=====
		frame_1 = video.get_child('frame_1')
		frame_2 = video.get_child('frame_2')
		frame_3 = video.get_child('frame_3')
		self.assertTrue(frame_1['skeleton'] == skel)
		self.assertTrue('skeleton' in frame_1.present_items)
		self.assertTrue(frame_2['skeleton'] is None)
		self.assertTrue('skeleton' in frame_2.absent_items)
		self.assertTrue(frame_3['skeleton'] is None)	
		self.assertFalse('skeleton' in frame_3.present_items)


		#=====[ Delete it again	]=====
		del frame_1['skeleton']
		self.assertTrue(frame_1['skeleton'] is None)
		self.assertFalse('skeleton' in frame_1.present_items)

		#=====[ Remove item from schema	]=====
		client.delete_item(Frame, 'skeleton')
		frame_1 = video.get_child('frame_1')




