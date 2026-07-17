from intracranial_ephys_utils.load_data import read_file, read_task_ncs, get_event_times
from ephyviewer import mkQApp, MainViewer, TraceViewer
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import os
import glob

def overview_ncs(recording_folder):
	'''
	Automatically plots a task recording folder (folder including electrode recordings [.ncs]; optional event information [.nev], spike-sorted single-units [.nse]) by frequency. 
	Also prints out all sampling frequencies [arr] and Event titles.
	:param recording_folder
	'''
	recording_folder = Path(recording_folder)
	file_types = ["ncs", "nse", "nev"]
	folder_dict = group_types_by_folder(recording_folder)
	for folder, vals in folder_dict.items():
		if ".ncs" not in vals:
			continue
		event_times, event_labels, global_start, event_files = [], [], None, []
		if ".nev" in vals:
			try:
				event_times, event_labels, global_start, event_files = get_event_times(folder)
				print("Events:", event_labels)
			except Exception as e:
				print("Event read failed:", e)
		rate_groups = group_by_rate(vals[".ncs"])
		for rate, files in rate_groups.items():
			data, names, r = load_group(folder, files)
			#plot_stack(data, names, rate, folder, event_times, global_start)
			view_stack(data, names, r, folder)
	
#overview_ncs(str(input("Type or Copy the recording folder pathway:")))

def find_files_of_type(directory: Path, file_type: str, recurse: bool = False) -> list[Path]:
	'''
	'''
	if recurse:
		files = list(directory.rglob("*."+file_type))
	else:
		files =  list(directory.glob("*."+file_type))
	return files

def group_types_by_folder(original_dir: Path) -> dict[Path, dict[str, list[Path]]]:
	'''
	Preserves the folder hierarchies by segmenting each parent folder into its contents by file_type.
	Takes a folder Path and returns a dictionary with key as parent directory and value as another dictionary with keys as file types and values as list of corresponding
	 file directories
	'''
	folder_groups = {}
	all_files =  original_dir.rglob("*")
	for file in all_files:
		parent_folder = file.parent
		if parent_folder not in folder_groups:
			folder_groups[parent_folder] = {}
		if file.suffix not in folder_groups[parent_folder]:
			folder_groups[parent_folder][file.suffix] = []
		folder_groups[parent_folder][file.suffix].append(file)
	return folder_groups

def group_by_rate(ncs_folder: list[Path]) -> dict[float, list[Path]]:
	'''
	Takes a list of (.ncs) Paths and returns a dictionary with key as sampling rate (Hz) and value as a lust
	'''
	grouped = {}
	for file in ncs_folder:
		ncs_reader = read_file(file)
		ncs_reader.parse_header()
		rate = ncs_reader.get_signal_sampling_rate()
		if rate not in grouped:
			grouped[rate] = []
		grouped[rate].append(file)
	return grouped

def load_group(folder, files):
	'''
	Takes a folder and file and returns a 2D NP Array of the signal (data), the names of files, and the sampling rate.
	'''
	signals = []
	names = []
	for file in files:
		signal, rate, intp, timestamps = read_task_ncs(folder, file.name)
		print(f"Reading Header: {file.name}")
		signals.append(signal)
		names.append(file.stem)
	minimum_len = min(len(sig) for sig in signals)
	signals = [sig[:minimum_len] for sig in signals]
	data = np.vstack(signals)
	return data, names, rate

def view_stack(data, names, rate, folder):
	'''
	Opens interactive scrollable ephyviewer window for a stack of channels
	'''
	#annotations_dir = Path.home() / "annotations"
	#os.makedirs(annotations_dir, exist_ok=True)
	#data_clean_viewer(subject=folder.name, session="1", annotations_directory=annotations_dir, electrode_names=names, dataset=data, fs=rate)
	
	app = mkQApp()
	wind = MainViewer(debug=False, show_auto_scale=True)
	view = TraceViewer.from_numpy(data.T, rate, 0., f'{folder.name} {rate}Hz', channel_names=names)
	view.params['scale_mode'] = 'same_for_all'
	view.params['display_labels'] = True
	view.auto_scale()
	wind.add_view(view)
	wind.show()
	app.exec()

def plot_stack(data, names, rate, folder, event_times=None, global_start=None):
	'''
	Plots a stack of files (electrodes) with event markers (if event_times are fed)
	'''
	n = data.shape[0] # num of channels (rows)
	figs, axes = plt.subplots(n, 1, sharex=True, figsize=(12, n/2))
	#  if there's a single chan, matplot won't register it as a list of axes (crash)
	if n == 1: axes = [axes]
	times = np.arange(data.shape[1]) / rate
	
	for i in range(n):
		axes[i].plot(times, data[i], linewidth=0.25)
		axes[i].set_ylabel(names[i], rotation=0, labelpad=30, fontsize=5)
		axes[i].set_yticks([]) # deletes volt nums on y ax-s
		if event_times is not None and global_start is not None:
			for event in event_times:
				axes[i].axvline((event * 1e-6) - global_start, color='r', linewidth=0.5)
	axes[-1].set_xlabel('Time (s)')
	axes[-1].set_xlim(0, 5)
	plt.suptitle(f'{rate} Hz - {folder.name}')
	plt.tight_layout()
	plt.show()












