import maya.cmds as cmds
import os as OS
import time as TIME


# Class for single row representing a single scenefile
class RenderRow:
          # Single row UI
   def __init__(self, globl, num):   
       # Represents global parent of all scenefiles in queue
       self.globl = globl

       self.layout = cmds.rowLayout(numberOfColumns=9)
       self.num = cmds.text(num)
       self.filepath = cmds.textField(placeholderText="scenefile")
       cmds.button(label="browse", command=self.browse_files)
       self.camera_id = cmds.textField(placeholderText="cameraID")
       cmds.text(label="start frame")
       self.start_frame = cmds.intField(value=0, width=40)
       cmds.text(label="end frame")
       self.end_frame = cmds.intField(value=1, width=40)
       cmds.button(label='-', command=self.delete_self)

       # Set parent, child hierarchy for deletion
       cmds.setParent("..")

   # Function to browse for file via file explorer/Finder
   def browse_files(self, *_):
       # File filters
       maya_files = "Maya Files (*.ma, *.mb)"
       res = cmds.fileDialog2(fileMode=1, fileFilter=maya_files, dialogStyle=1)
       if res:
           # Set text and variable as the browsed file's path
           cmds.textField(self.filepath, e=True, text=res[0])


   # Function for removing scenefile from queue
   def delete_self(self, *_):
       # Remove scenefile from global control
       if self in self.globl.rows:
           self.globl.rows.remove(self)


       # Remove scenefile from UI
       cmds.deleteUI(self.layout)


# Class to represent Batch Renderer
class BatchRender:
   def __init__(self):
       self.rows = []
       self.windowID = 'batchRenderWindow'


       # Remove window if already exists
       if cmds.window (self.windowID, exists=True):
           cmds.deleteUI(self.windowID)


       # Global UI
       self.window = cmds.window(self.windowID, title='Render Queue', resizeToFitChildren=True)
       self.layout = cmds.columnLayout(adjustableColumn=True, columnAlign='center')
       cmds.separator(h=12, style='none')
       cmds.text("Queue files to be rendered.")
       cmds.separator(h=12, style='none')
       cmds.rowLayout(numberOfColumns=3)

       self.output_folder = cmds.textField(placeholderText="output path", width=200)
       cmds.button(label='Browse', command=self.browse_files)
       cmds.button(label='+', command=self.add_row)
       cmds.setParent("..")

       cmds.separator(h=12, style='none')
       cmds.button(label='Batch Render', command=self.batch_render)
       cmds.separator(h=12, style='none')

       # Display the window
       cmds.showWindow()

   # Function to browse for output folder via file explorer/Finder
   def browse_files(self, *_):
       res = cmds.fileDialog2(fileMode=3, dialogStyle=1)
       if res:
           # Set text and variable as the folder's
           cmds.textField(self.output_folder, e=True, text=res[0])

   # Add scenefile to queue
   def add_row(self, *_):
       row = RenderRow(self, len(self.rows))
       self.rows.append(row)
  
   # Render all scenefiles in queue
   def batch_render(self, *_):
       print("-- BEGIN BATCH RENDER --")

       if len(self.rows) < 1:
           print("No files queued for batch render.")

       for scene in self.rows:
           scene_file = cmds.textField(scene.filepath, q=True, text=True)
           camera_id = cmds.textField(scene.camera_id, q=True, text=True)
           start_frame = cmds.intField(scene.start_frame, q=True, value=True)
           end_frame = cmds.intField(scene.end_frame, q=True, value=True)

           if OS.path.exists(scene_file):
               self.render_camera(scene_file, camera_id, start_frame, end_frame)
           else:
               print(f"INVALID scene filepath {scene_file}.")
               continue


   # Render single scenefile   
   def render_camera(self, scene_file, camera_id, start_frame, end_frame):
       # Check if output folder is valid
       output_folder_text = cmds.textField(self.output_folder, q=True, text=True)
       if not OS.path.exists(output_folder_text):
           print(f"Invalid output folder {output_folder_text}")
           return

       print(f"Rendering camera: {camera_id}.")

       # loading scenefile
       cmds.file(scene_file, open=True, force=True)

       # setup frame range
       cmds.setAttr("defaultRenderGlobals.startFrame", start_frame)
       cmds.setAttr("defaultRenderGlobals.endFrame", end_frame)
       print("Successfully set frame range.")

       # Find cameras and check if valid
       all_cameras = cmds.ls(cameras=True)
       camera_shape = camera_id
       if camera_shape in all_cameras:
               print(f"Preparing to render camera {camera_shape}.")

                # Setup output
               camera_folder = OS.path.join(output_folder_text, camera_id)

               # Create output folder if it does not exist
               if not OS.path.exists(camera_folder):
                   OS.makedirs(camera_folder)
               print("Outputing to folder " + camera_folder)

                # Set filenames to include camera id
               prefix = OS.path.join(camera_folder, camera_id)
               cmds.setAttr("defaultRenderGlobals.imageFilePrefix", prefix, type="string")

               # Set attribute to render in TIFF format
               cmds.setAttr("defaultRenderGlobals.imageFormat", 3)

               # Disable all AOVs besides beauty
               aovs_list = cmds.ls(type='aiAOV')
               if aovs_list:
                   for aov in aovs_list:
                       cmds.setAttr(aov + '.enabled', False)

               # Look through selected camera
               cmds.lookThru(camera_id)

               # Set selected camera to renderable, rest to false
               for cam in all_cameras:
                   cmds.setAttr(f"{cam}.renderable", False)

               # Only set selected camera to renderable
               cmds.setAttr(f"{camera_shape}.renderable", True)

               render_start = TIME.time()
               try:
                   cmds.arnoldRender(batch=True)
                   render_time_elapsed = TIME.time() - render_start

                   # Print time taken for scenefile render
                   print(
                       f"Render Completed : Camera={camera_id} : "
                       f"in {render_time_elapsed:.0f} seconds "
                       f"({render_time_elapsed/60:.1f} minutes)"
                   )
               except Exception as e:
                   print(f"Render ERROR {e}")
              
               # File system cooldown
               TIME.sleep(1)
       else:
           print(f"Camera {camera_id}  not found.")

# Run script
BatchRender()

