import sublime
import sublime_plugin

import os
import json

def walk_up(bottom):
	"""
	mimic os.walk, but walk 'up'
	instead of down the directory tree
	"""

	bottom = os.path.realpath(bottom)

	#get files in current dir
	try:
		names = os.listdir(bottom)
	except Exception as e:
		print(e)
		return


	dirs, nondirs = [], []
	for name in names:
		if os.path.isdir(os.path.join(bottom, name)):
			dirs.append(name)
		else:
			nondirs.append(name)

	yield bottom, dirs, nondirs

	new_path = os.path.realpath(os.path.join(bottom, '..'))

	# see if we are at the top
	if new_path == bottom:
		return

	for x in walk_up(new_path):
		yield x


def find_node_modules(search_dir):
	node_modules_dirs = []

	all_deps = []

	for c, d, f in walk_up(search_dir):
		if 'package.json' in f:
			with open(os.path.join(c, 'package.json')) as package_json:
				data = json.load(package_json)

				all_deps += list(data.get('dependencies', {}).keys())
				all_deps += list(data.get('devDependencies', {}).keys())
	return all_deps


def list_dir(search_dir, search_term):
	print('search_dir', search_dir)
	try:
		temp_dir_contents = os.listdir(search_dir)
		# print(temp_dir_contents)

		prefix = ''

		if not search_term.endswith('/'):
			prefix = '/'

		print('prefix:', prefix, search_term)

		dir_contents = []
		for p in temp_dir_contents:
			if os.path.isdir(os.path.join(search_dir, p)):
				dir_contents.append(p + '/')
			else:
				dir_contents.append(p)

		if not search_term.startswith('.'):
			node_modules = find_node_modules(search_dir)
		else:
			node_modules = []

		prefixed_dir_contents = [prefix + p for p in dir_contents]

		all_dir_contents = prefixed_dir_contents + node_modules
		print('all_dir_contents', all_dir_contents)

		return [[p, p] for p in all_dir_contents]
	except FileNotFoundError as e:
		parent_dir = os.path.dirname(search_dir)
		return list_dir(parent_dir, search_term)


class ExampleCommand(sublime_plugin.EventListener):
	def on_query_completions(self, view, prefix, locations):
		if not view.match_selector(locations[0], 'source.js'):
			return None

		line_region = view.line(locations[0])
		line_str = view.substr(line_region)

		if not line_str.startswith('import '):
			return None

		file_name = view.file_name()
		current_dir = os.path.dirname(file_name)

		try:
			search_term = line_str.split('from \'')[1].split('\'')[0]
			search_dir = os.path.join(
				current_dir,
				search_term
			)
		except Exception as e:
			return None

		return list_dir(search_dir, search_term)
