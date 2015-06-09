package gnue.forms.ui;

import javax.swing.*;
import javax.swing.event.*;
import javax.swing.filechooser.FileFilter;
import org.apache.commons.io.filefilter.WildcardFileFilter;
import java.awt.*;
import java.awt.event.*;
import org.json.*;
import java.util.*;
import java.net.*;
import java.io.*;
import pub.Base64;
import gnue.forms.components.MessageDetailsDialog;
import gnue.forms.components.Utils;

public abstract class FrameAbstract extends Widget {

	static private final int URL_DL_BUF_SIZE = 65536;

	private Widget toolBar = null;  // used in uiSetToolbar
	private Widget statusBar = null;

	protected boolean maximizable = true;
	protected boolean iconifiable = true;
	protected boolean resizable = true;
	protected boolean closable = true;
	protected boolean maximize = false;

	public FrameAbstract(Desktop desktop, Integer id) {
		super(desktop, id);
	}
	
	public FrameAbstract(Desktop desktop, Integer id, JSONArray windowStyle) {
		super(desktop, id);
		for (int i=0; i<windowStyle.length(); i++) {
			String style = windowStyle.getString(i);
			if (style.equals("-MINIMIZE_BOX")) {
				iconifiable = false;
			} else if (style.equals("-MAXIMIZE_BOX")) {
				maximizable = false;
			} else if (style.equals("-CLOSE_BOX")) {
				closable = false;
			} else if (style.equals("-RESIZEABLE")) {
				resizable = false;
			} else if (style.equals("MAXIMIZE")) {
				maximize = true;
			}
		}
	}

	abstract public void uiFit();
	abstract public void uiShow(Boolean modal);
	abstract public void uiClose();
	abstract public void uiDestroy();
	abstract public void uiSetTitle(String title);

	public void uiAdd(Widget widget) {
		getComponent().add(widget.getComponent());
	}

	abstract public void uiSetMenuBar(Widget menuBar);

	public void uiSetToolBar(Widget toolBar) {
		if (this.toolBar != toolBar) {
			if (this.toolBar != null) {
				getComponent().remove(this.toolBar.getComponent());
			}
			if (toolBar != null) {
				getComponent().add(toolBar.getComponent(), BorderLayout.NORTH);
			}
			getComponent().revalidate();
			this.toolBar = toolBar;
		}
	}

	public void uiRemoveToolBar() {
		uiSetToolBar(null);
	}

	public void uiSetStatusBar(Widget statusBar) {
		if (this.statusBar != statusBar) {
			if (this.statusBar != null) {
				getComponent().remove(this.statusBar.getComponent());
			}
			if (statusBar != null) {
				getComponent().add(statusBar.getComponent(), BorderLayout.SOUTH);
			}
			this.statusBar = statusBar;
		}
	}

	public void uiRemoveStatusBar() {
		uiSetStatusBar(null);
	}

	/**
	 *  This function creates a message box of a given kind and returns True,
	 *  False or None depending on the button pressed.
	 *
	 *  @param message: the text of the messagebox
	 *  @param kind: type of the message box. Valid types are 'Info',
	 *			'Warning', 'Question', 'Error'
	 *  @param title: title of the message box
	 *  @param cancel: If True a cancel button will be added to the dialog
	 *
	 *  @return: True if the Ok-, Close-, or Yes-button was pressed, False if
	 *			the No-button was pressed or None if the Cancel-button was pressed.
	 */
	public void uiShowMessage(String message, String kind, String title, Boolean cancel, Boolean hasResultConsumer) {
		kind = kind.toLowerCase();

		int messageType = JOptionPane.PLAIN_MESSAGE;
		int optionType = JOptionPane.DEFAULT_OPTION;

		if ("info".equals(kind)) {
			messageType = JOptionPane.INFORMATION_MESSAGE;
		}
		else if ("warning".equals(kind)) {
			messageType = JOptionPane.WARNING_MESSAGE;
		}
		else if ("error".equals(kind)) {
			messageType = JOptionPane.ERROR_MESSAGE;
		}
		else if ("question".equals(kind)) {
			messageType = JOptionPane.QUESTION_MESSAGE;
			optionType = cancel ? JOptionPane.YES_NO_CANCEL_OPTION : JOptionPane.YES_NO_OPTION;
		}
		
		//getDesktop().endWait();
		
		int iresult = JOptionPane.showConfirmDialog(
			getDesktop().getComponent(),
			message,
			title,
			optionType,
			messageType
		);
		
		//getDesktop().beginWait();

		if (hasResultConsumer) {
			Boolean result = null;
			if (iresult != JOptionPane.CANCEL_OPTION) {
				result = new Boolean(iresult == JOptionPane.YES_OPTION || iresult == JOptionPane.OK_OPTION);
			}
			call("onShowMessage", result);
		}
	}
	
	/**
	 *
	 *	Bring up a dialog for selecting filenames.
	 *
	 *	@param title: Message to show on the dialog
	 *	@param defaultDir: the default directory, or the empty string
	 *	@param defaultFile: the default filename, or the empty string
	 *	@param wildcard: a list of tuples describing the filters used by the
	 *	        dialog.  Such a tuple constists of a description and a fileter.
	 *	        Example: [('PNG Files', '*.png'), ('JPEG Files', '*.jpg')]
	 *	        If no wildcard is given, all files will match (*.*)
	 *	@param mode: Is this dialog an open- or a save-dialog.  If mode is
	 *	        'save' it is a save dialog, everything else would be an
	 *	        open-dialog.
	 *	@param multiple: for open-dialog only: if True, allows selecting
	 *	        multiple files
	 *	@param overwritePrompt: for save-dialog only: if True, prompt for a
	 *	        confirmation if a file will be overwritten
	 *	@param fileMustExist: if True, the user may only select files that
	 *	        actually exist
	 *
	 *	@returns: a sequence of filenames or None if the dialog has been
	 *	        cancelled.
	 */
	public void uiSelectFiles(String title, String defaultDir, String defaultFile, JSONArray wildcard, String mode, Boolean multiple, Boolean overwritePrompt, Boolean fileMustExist, Boolean readData) {
		JFileChooser fc = new JFileChooser(defaultDir);
		fc.setDialogTitle(title);
		if (defaultFile.length() > 0) {
			fc.setSelectedFile(new File(defaultDir, defaultFile));
		}
		fc.setMultiSelectionEnabled(multiple);
	
		// remove default filter if adding custom
		if (wildcard.length() > 0) {
			fc.setAcceptAllFileFilterUsed(false);
			//for (FileFilter ff: fc.getChoosableFileFilters()) {
			//	fc.removeChoosableFileFilter(ff);
			//}
		}
	
		// add custom file filters
		for (int i=0; i<wildcard.length(); i++) {
			JSONArray wc = wildcard.getJSONArray(i);
			String description = wc.getString(0);
			String mask = wc.getString(1);
			fc.addChoosableFileFilter(new WildcardFileChooserFilter(mask, description));
		}
		
		if (wildcard.length() > 0) {
			fc.setFileFilter(fc.getChoosableFileFilters()[0]);
		}
	
		int rc;
		boolean save = "save".equalsIgnoreCase(mode);
		if (save) {
			rc = fc.showSaveDialog(getComponent());
		}
		else {
			rc = fc.showOpenDialog(getComponent());
		}
		
		String[] pathes;
			
		if (rc == JFileChooser.APPROVE_OPTION) {
			File[] files;
			if (multiple) {
				files = fc.getSelectedFiles();
			}
			else {
				files = new File[]{fc.getSelectedFile()};
			}

			// fix path if save mode and path has wrong extension
			if (save && fc.getFileFilter() instanceof WildcardFileChooserFilter) {
				String extension = ((WildcardFileChooserFilter)fc.getFileFilter()).getExtension();
				if (extension != null) {
					for (int i=0; i<files.length; i++) {
						String path = files[i].getPath();
						if (!path.toLowerCase().endsWith(extension)) {
							files[i] = new File(path + extension);
						}
					}
				}
			}

			if (save && overwritePrompt) {
				for (File f: files) {
					if (f.exists()) {
						if (JOptionPane.OK_OPTION != JOptionPane.showConfirmDialog(getComponent(), "File '"+f.getPath()+"' exists, overwrite?", title, JOptionPane.OK_CANCEL_OPTION, JOptionPane.WARNING_MESSAGE)) {
							files = new File[0];
							//stem.out.println("USER DO NOT WANT OVERWRITE");
							break;
						}
					}
				}
			}
			if (!save && fileMustExist) {
				for (File f: files) {
					if (!f.exists()) {
						JOptionPane.showConfirmDialog(getComponent(), "File(s) must exist!", title, JOptionPane.DEFAULT_OPTION , JOptionPane.ERROR_MESSAGE);
						files = new File[0];
						//stem.out.println("MUST EXISTS BUT NOT");
						break;
					}
				}
			}
			
			pathes = new String[files.length];
			for (int i=0; i<files.length; i++) {
				pathes[i] = files[i].getPath();
				//stem.out.println(">>>" + pathes[i]);
			}
		}
		else {
			pathes = new String[0];
		}
		JSONArray result = new JSONArray(pathes);
		if (readData) {
			for (int i=0; i<result.length(); i++) {
				String filename = result.getString(i);
				String data = "";
				try {
					data = Base64.encodeFromFile(filename);
				}
				catch (IOException e) {
					e.printStackTrace();
				}
				result.put(i, new JSONArray(new String[]{filename, data}));
			}
		}
		call("onSelectFiles", result);
	}

	/**
	 * @param newDir is ignored
	 */
	public void uiSelectDir(String title, String defaultDir, Boolean newDir) {
		JFileChooser fc = new JFileChooser(defaultDir);
		fc.setDialogTitle(title);
		fc.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
		fc.setAcceptAllFileFilterUsed(false);
		String selectedDir = "";
		if (fc.showOpenDialog(getComponent()) == JFileChooser.APPROVE_OPTION) { 
			selectedDir = fc.getSelectedFile().getPath();
		}
		call("onSelectDir", selectedDir);
	}

	public void uiDownloadFile(String url, String filePath, Boolean quiet) {
		try {
			URLConnection uc = getDesktop().wrapUrl(url).openConnection();
			
			InputStream in = new BufferedInputStream(uc.getInputStream());
			FileOutputStream out = new FileOutputStream(filePath);
			
			byte[] data = new byte[URL_DL_BUF_SIZE];
			while (true) {
				int bytesRead = in.read(data);
				if (bytesRead == -1) {
					break;
				}
				out.write(data, 0, bytesRead);
		    }
			in.close();
			out.close();
			if (!quiet) {
				JOptionPane.showConfirmDialog(getComponent(), "File saved successfully: " + filePath, "File saving", JOptionPane.DEFAULT_OPTION, JOptionPane.INFORMATION_MESSAGE);
			}
		} 
		catch(IOException e) {
			e.printStackTrace();
			JOptionPane.showConfirmDialog(getComponent(), "Error while saving file '" + filePath + "': " + e.getClass().getName() + ": " + e.getMessage(), "File saving", JOptionPane.DEFAULT_OPTION, JOptionPane.ERROR_MESSAGE);
		}
	}
	
	public void uiStartFile(String url, String fileName) {
		try {
			File file = File.createTempFile("harm_start_", fileName);
			uiDownloadFile(url, file.getAbsolutePath(), true);
			Runtime.getRuntime().exec("rundll32 SHELL32.DLL,ShellExec_RunDLL " + file.getAbsolutePath());
		} 
		catch(IOException e) {
			e.printStackTrace();
			JOptionPane.showConfirmDialog(getComponent(), "Error while starting file: " + e.getClass().getName() + ": " + e.getMessage(), "File saving", JOptionPane.DEFAULT_OPTION, JOptionPane.ERROR_MESSAGE);
		}
	}

	public void uiUploadFile(String filePath, String url) {
		try {
			File file = new File(filePath);
			URLConnection uc = getDesktop().wrapUrl(url).openConnection();
			
			uc.setDoOutput(true);
			
			// Don't use a cached version of URL connection.
			uc.setUseCaches(false);
			uc.setDefaultUseCaches(false);
			
			uc.setRequestProperty("Content-Type", "application/octet-stream");
			uc.setRequestProperty("Content-Length", Long.toString(file.length()));
			
			// create file stream and write stream to write file data.
			FileInputStream fis = new FileInputStream(file);
			OutputStream os = uc.getOutputStream();
			
			try {
				byte[] buffer = new byte[4096];
				while (true) {
					int bytes = fis.read(buffer);
					if (bytes < 0) break;
					os.write(buffer, 0, bytes);
				}
				os.flush();
			}
			finally {
				os.close();
				fis.close();
			}
				
			BufferedReader reader = new BufferedReader(new InputStreamReader(uc.getInputStream(), "windows-1251"));
			String response = reader.readLine();
			
			call("onUploadFile", response);
		}
		catch (IOException e) {
			e.printStackTrace();
			JOptionPane.showConfirmDialog(getComponent(), "Error while uploading file: " + e.getClass().getName() + ": " + e.getMessage(), "File saving", JOptionPane.DEFAULT_OPTION, JOptionPane.ERROR_MESSAGE);
		}
	}

	public void uiShowException(String group, String name, String message, String detail) {
		new MessageDetailsDialog(getComponent(), "Unexpected error", "Group: " + group + "\n" + name + ": " + message, detail, JOptionPane.ERROR_MESSAGE, false);
	}

	public void uiBeep() {
		Toolkit.getDefaultToolkit().beep();
	}
	
	public void uiCallAfter() {
		call("onCallAfter");
	}

	static class WildcardFileChooserFilter extends FileFilter {
		
		private WildcardFileFilter delegate;
		private String description;
		private String wildcard;
		
		public WildcardFileChooserFilter(String wildcard, String description) {
			this.description = description;
			this.wildcard = wildcard;
			this.delegate = new WildcardFileFilter(wildcard);
		}
		
		public boolean accept(File pathName) {
			return pathName.isDirectory() || delegate.accept(pathName);
		}
		
		public String getDescription() {
			return description;
		}
		
		public String getExtension() {
			if (wildcard.startsWith("*.")) {
				String extension = wildcard.substring(1).toLowerCase();
				if (extension.indexOf("*") == -1) {
					return extension;
				}
			}
			return null;
		}
		
	}
	
}

