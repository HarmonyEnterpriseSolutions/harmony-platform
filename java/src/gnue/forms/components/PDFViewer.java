/*
 * $Id: PDFViewer.java,v 1.7 2011/07/20 22:50:24 oleg Exp $
 *
 * Copyright 2004 Sun Microsystems, Inc., 4150 Network Circle,
 * Santa Clara, California 95054, U.S.A. All rights reserved.
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */
package gnue.forms.components;


import java.awt.*;
import java.awt.event.*;
import java.awt.geom.Rectangle2D;
import java.awt.print.*;
import javax.print.*;
import javax.print.attribute.*;
import javax.print.attribute.standard.*;
import java.beans.PropertyChangeEvent;
import java.beans.PropertyChangeListener;
import java.io.*;
import java.net.*;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;

import java.util.logging.Level;
import java.util.logging.Logger;
import javax.swing.*;
import javax.swing.filechooser.FileFilter;
import javax.swing.SwingUtilities;
import com.sun.pdfview.action.GoToAction;
import com.sun.pdfview.action.PDFAction;
import java.lang.reflect.InvocationTargetException;

import com.sun.pdfview.*;

/**
 * A demo PDF Viewer application.
 */
public class PDFViewer extends JPanel implements KeyListener, PageChangeListener {

	static float ZOOM_FACTOR = 1.2f;
	static int MIN_ZOOM_SIZE = 100;
	static int MAX_ZOOM_SIZE = 4000;

	/** The current PDFFile */
	PDFFile curFile;
	/** the name of the current document */
	String docName;
	/** The split between thumbs and page */
	JSplitPane split;
	/** The thumbnail scroll pane */
	JScrollPane thumbscroll;
	/** The thumbnail display */
	ThumbPanel thumbs;
	/** The page display */
	PDFPanel page;

	JScrollPane scrollPage;

	PageFormat pageFormat;

	//	  Thread anim;
	/** The current page number (starts at 0), or -1 if no page */
	int currentPage = -1;
	/** the current page number text field */
	JTextField pageField;
	/** true if the thumb panel should exist at all */
	boolean useThumbs = true;
	/** flag to indicate when a newly added document has been announced */
	Flag docWaiter;
	/** the document menu */
	JMenu docMenu;

	/**
	 * utility method to get an icon from the resources of this class
	 * @param name the name of the icon
	 * @return the icon, or null if the icon wasn't found.
	 */
	private Icon getIcon(String name) {
		Icon icon = null;
		URL url = null;
		try {
			url = getClass().getResource(name);

			icon = new ImageIcon(url);
			if (icon == null) {
				System.out.println("Couldn't find " + url);
			}
		} catch (Exception e) {
			System.out.println("Couldn't find " + getClass().getName() + "/" + name);
			e.printStackTrace();
		}
		return icon;
	}

	/// FILE MENU
	/*Action openAction = new AbstractAction("Open...") {
		public void actionPerformed(ActionEvent evt) {
			doOpen();
		}
	};*/

	/*Action saveAction = new AbstractAction("Save...", getIcon("icons/pdf-save.gif")) {
		public void actionPerformed(ActionEvent evt) {
			doOpen();
		}
	};*/

	//Action pageSetupAction = new AbstractAction("Page setup...") {
	//	  public void actionPerformed(ActionEvent evt) {
	//		  doPageSetup();
	//	  }
	//};

	Action printAction = new AbstractAction("Print...", getIcon("icons/pdf-print.gif")) {
		public void actionPerformed(ActionEvent evt) {
			doPrint();
		}
	};

	Action closeAction = new AbstractAction("Close") {
		public void actionPerformed(ActionEvent evt) {
			doClose();
		}
	};

	class ZoomAction extends AbstractAction {

		float zoomfactor;

		public ZoomAction(String name, Icon icon, float factor) {
			super(name, icon);
			zoomfactor = factor;
		}

		public void actionPerformed(ActionEvent evt) {
			doZoom(zoomfactor);
		}
	}

	ZoomAction zoomInAction  = new ZoomAction("Zoom in", getIcon("icons/pdf-zoomin.gif"), ZOOM_FACTOR);
	ZoomAction zoomOutAction = new ZoomAction("Zoom out", getIcon("icons/pdf-zoomout.gif"), 1f/ZOOM_FACTOR);

	class FitAction extends AbstractAction {
		boolean width;
		boolean height;

		public FitAction(String name, Icon icon, boolean width, boolean height) {
			super(name, icon);
			this.width  = width;
			this.height = height;
		}

		public void actionPerformed(ActionEvent evt) {
			doFit(width, height);
		}
	}

	Action fitAction = new FitAction("Fit", getIcon("icons/pdf-fit.gif"), true, true);
	Action fitHeightAction = new FitAction("Fit height", getIcon("icons/pdf-fit-height.gif"), true, false);

	class ThumbAction extends AbstractAction implements PropertyChangeListener {

		boolean isOpen = true;

		public ThumbAction() {
			super("Hide thumbnails");
		}

		public void propertyChange(PropertyChangeEvent evt) {
			int v = ((Integer) evt.getNewValue()).intValue();
			if (v <= 1) {
				isOpen = false;
				putValue(ACTION_COMMAND_KEY, "Show thumbnails");
				putValue(NAME, "Show thumbnails");
			} else {
				isOpen = true;
				putValue(ACTION_COMMAND_KEY, "Hide thumbnails");
				putValue(NAME, "Hide thumbnails");
			}
		}

		public void actionPerformed(ActionEvent evt) {
			doThumbs(!isOpen);
		}
	}

	ThumbAction thumbAction = new ThumbAction();

	Action firstAction = new AbstractAction("First", getIcon("icons/pdf-first.gif")) {
		public void actionPerformed(ActionEvent evt) {
			gotoPage(0);
		}
	};

	Action lastAction = new AbstractAction("Last", getIcon("icons/pdf-last.gif")) {
		public void actionPerformed(ActionEvent evt) {
			gotoPage(getPageCount()-1);
		}
	};

	Action prevAction = new AbstractAction("Prev", getIcon("icons/pdf-prev.gif")) {
		public void actionPerformed(ActionEvent evt) {
			incPage(-1);
		}
	};

	Action nextAction = new AbstractAction("Next", getIcon("icons/pdf-next.gif")) {
		public void actionPerformed(ActionEvent evt) {
			incPage(+1);
		}
	};

	/**
	 * Create a new PDFViewer based on a user, with or without a thumbnail
	 * panel.
	 * @param useThumbs true if the thumb panel should exist, false if not.
	 */
	public PDFViewer(boolean useThumbs) {
		super();
		this.useThumbs = useThumbs;

		setLayout(new BorderLayout());

		page = new PDFPanel();
		page.addKeyListener(this);

		scrollPage = new JScrollPane(page);

		if (useThumbs) {
			split = new JSplitPane(split.HORIZONTAL_SPLIT);
			split.addPropertyChangeListener(split.DIVIDER_LOCATION_PROPERTY, thumbAction);
			split.setOneTouchExpandable(true);
			thumbs = new ThumbPanel(null);
			thumbscroll = new JScrollPane(thumbs,
					thumbscroll.VERTICAL_SCROLLBAR_ALWAYS,
					thumbscroll.HORIZONTAL_SCROLLBAR_NEVER);
			split.setLeftComponent(thumbscroll);
			split.setRightComponent(scrollPage);
			add(split, BorderLayout.CENTER);
		} else {
			add(scrollPage, BorderLayout.CENTER);
		}

		JToolBar toolbar = new JToolBar();
		toolbar.setFloatable(false);

		toolbar.add(printAction);
		//toolbar.add(pageSetupAction);
		//toolbar.add(saveAction);

		toolbar.addSeparator();
		toolbar.add(firstAction);
		toolbar.add(prevAction);
		toolbar.add(nextAction);
		toolbar.add(lastAction);
		toolbar.addSeparator();

		pageField = new JTextField("-", 3);
		//  pageField.setEnabled(false);
		pageField.setMaximumSize(new Dimension(45, 36));
		pageField.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent evt) {
				int pagenum = -1;
				try {
					pagenum = Integer.parseInt(pageField.getText()) - 1;
				} catch (NumberFormatException nfe) {
				}
				if (pagenum >= curFile.getNumPages()) {
					pagenum = curFile.getNumPages() - 1;
				}
				if (pagenum >= 0) {
					if (pagenum != currentPage) {
						gotoPage(pagenum);
					}
				} else {
					pageField.setText(String.valueOf(currentPage));
				}
			}
		});
		toolbar.add(pageField);

		toolbar.addSeparator();

		toolbar.add(zoomInAction);
		toolbar.add(zoomOutAction);

		toolbar.addSeparator();

		toolbar.add(fitHeightAction);
		toolbar.add(fitAction);

		for (Component c: toolbar.getComponents()) {
			if (c instanceof JButton) {
				((JButton)c).setMargin(new Insets(0,0,0,0));
				((JButton)c).setFocusable(false);

			}
		}

		add(toolbar, BorderLayout.NORTH);

		setEnabling();

		Dimension screen = Toolkit.getDefaultToolkit().getScreenSize();
		int x = (screen.width - getWidth()) / 2;
		int y = (screen.height - getHeight()) / 2;
		setLocation(x, y);
		if (SwingUtilities.isEventDispatchThread()) {
			setVisible(true);
		} else {
			try {
				SwingUtilities.invokeAndWait(new Runnable() {

					public void run() {
						setVisible(true);
					}
				});
			} catch (InvocationTargetException ie) {
				// ignore
			} catch (InterruptedException ie) {
				// ignore
			}
		}
	}

	/**
	 * Increments page
	 * @param increment page increment
	 */
	public void incPage(int increment) {
		if (curFile != null) {
			int i = currentPage+increment;
			if (i >= 0 && i < curFile.getNumPages()) {
				gotoPage(i);
			}
		}
	}
	
	public int getPageCount() {
		return curFile.getNumPages();
	}

	/**
	 * Changes the displayed page. Zero based.
	 * @param pagenum the page to display
	 */
	public void gotoPage(int index) {
		if (index < 0) {
			index += curFile.getNumPages();
		}

		//ystem.out.println("Going to page " + pagenum);
		currentPage = Math.max(0, Math.min(curFile.getNumPages()-1, index));;

		// update the page text field
		pageField.setText(String.valueOf(currentPage + 1));

		// fetch the page and show it in the appropriate place
		PDFPage pg = curFile.getPage(currentPage + 1);
		page.showPage(pg);
		page.requestFocus();

		// update the thumb panel
		if (useThumbs) {
			thumbs.pageShown(currentPage);
		}

		setEnabling();
	}


	/**
	 * Enable or disable all of the actions based on the current state.
	 */
	public void setEnabling() {
		boolean fileavailable = curFile != null;
		boolean pageshown = page.getPage() != null;
		boolean printable = fileavailable && curFile.isPrintable();

		pageField.setEnabled(fileavailable);

		printAction.setEnabled(printable);
		//saveAction.setEnabled(fileavailable);
		closeAction.setEnabled(fileavailable);

		boolean prevEnabled = pageshown && currentPage > 0;
		boolean nextEnabled = pageshown && currentPage < curFile.getNumPages()-1;

		firstAction.setEnabled(prevEnabled);
		lastAction.setEnabled(nextEnabled);

		prevAction.setEnabled(prevEnabled);
		nextAction.setEnabled(nextEnabled);

		fitAction.setEnabled(pageshown);
		fitHeightAction.setEnabled(pageshown);

		zoomInAction.setEnabled(pageshown);
		zoomOutAction.setEnabled(pageshown);
	}

	/**
	 * open a URL to a PDF file. The file is read in and processed
	 * with an in-memory buffer.
	 *
	 * @param url
	 * @throws java.io.IOException
	 */
	public void openFile(URL url) throws IOException {
		URLConnection urlConnection = url.openConnection();
		int contentLength = urlConnection.getContentLength();
		InputStream istr = urlConnection.getInputStream();
		ByteBuffer buf;
		if (contentLength > 0) {
			byte[] byteBuf = new byte[contentLength];
			int offset = 0;
			int read = 0;
			while (read >= 0) {
				read = istr.read(byteBuf, offset, contentLength - offset);
				if (read > 0) {
					offset += read;
				}
			}
			if (offset != contentLength) {
				throw new IOException("Could not read all of URL file.");
			}
			buf = ByteBuffer.allocate(contentLength);
			buf.put(byteBuf);
		}
		else {
			ByteArrayOutputStream baos = new ByteArrayOutputStream();
			int c;
			while ((c = istr.read()) != -1) {
				baos.write((char)c);
			}
			buf = ByteBuffer.wrap(baos.toByteArray());
		}
		openPDFByteBuffer(buf, url.toString(), url.getFile());
	}

	/**
	 * <p>Open a specific pdf file.  Creates a DocumentInfo from the file,
	 * and opens that.</p>
	 *
	 * <p><b>Note:</b> Mapping the file locks the file until the PDFFile
	 * is closed.</p>
	 *
	 * @param file the file to open
	 * @throws IOException
	 */
	public void openFile(File file) throws IOException {
		// first open the file for random access
		RandomAccessFile raf = new RandomAccessFile(file, "r");

		// extract a file channel
		FileChannel channel = raf.getChannel();

		// now memory-map a byte-buffer
		ByteBuffer buf =
				channel.map(FileChannel.MapMode.READ_ONLY, 0, channel.size());
		openPDFByteBuffer(buf, file.getPath(), file.getName());
	}

	/**
	 * <p>Open a specific pdf file.  Creates a DocumentInfo from the file,
	 * and opens that.</p>
	 *
	 * <p><b>Note:</b> By not memory mapping the file its contents are
	 * not locked down while PDFFile is open.</p>
	 *
	 * @param file the file to open
	 */
	public void openFileUnMapped(File file) throws IOException {
		DataInputStream istr = null;
		try {
			//load a pdf from a byte buffer
			// avoid using a RandomAccessFile but fill a ByteBuffer directly
			istr = new DataInputStream(new FileInputStream(file));
			long len = file.length();
			if (len > Integer.MAX_VALUE) {
				throw new IOException("File too long to decode: " + file.getName());
			}
			int contentLength = (int) len;
			byte[] byteBuf = new byte[contentLength];
			int offset = 0;
			int read = 0;
			while (read >= 0) {
				read = istr.read(byteBuf, offset, contentLength - offset);
				if (read > 0) {
					offset += read;
				}
			}
			ByteBuffer buf = ByteBuffer.allocate(contentLength);
			buf.put(byteBuf);
			openPDFByteBuffer(buf, file.getPath(), file.getName());
		} catch (FileNotFoundException fnfe) {
			fnfe.printStackTrace();
		} catch (IOException ioe) {
			ioe.printStackTrace();
		} finally {
			if (istr != null) {
				try {
					istr.close();
				} catch (Exception e) {
					// ignore error on close
				}
			}
		}
	}

	/**
	 * open the ByteBuffer data as a PDFFile and start to process it.
	 *
	 * @param buf
	 * @param path
	 */
	private void openPDFByteBuffer(ByteBuffer buf, String path, String name) {

		// create a PDFFile from the data
		PDFFile newfile = null;
		try {
			newfile = new PDFFile(buf);
		} catch (IOException ioe) {
			openError(path + " doesn't appear to be a PDF file.");
			return;
		}

		// Now that we're reasonably sure this document is real, close the
		// old one.
		doClose();

		// set up our document
		this.curFile = newfile;
		docName = name;

		// set up the thumbnails
		if (useThumbs) {
			thumbs = new ThumbPanel(curFile);
			thumbs.addPageChangeListener(this);
			thumbscroll.getViewport().setView(thumbs);
			thumbscroll.getViewport().setBackground(Color.gray);
		}

		setEnabling();

		// display page 1.
		gotoPage(0);
	}

	/**
	 * Display a dialog indicating an error.
	 */
	public void openError(String message) {
		JOptionPane.showMessageDialog(split, message, "Error opening file",
				JOptionPane.ERROR_MESSAGE);
	}
	/**
	 * A file filter for PDF files.
	 */
	FileFilter pdfFilter = new FileFilter() {

		public boolean accept(File f) {
			return f.isDirectory() || f.getName().endsWith(".pdf");
		}

		public String getDescription() {
			return "Choose a PDF file";
		}
	};
	private File prevDirChoice;

	/*
	 * Ask the user for a PDF file to open from the local file system
	public void doOpen() {
		try {
			JFileChooser fc = new JFileChooser();
			fc.setCurrentDirectory(prevDirChoice);
			fc.setFileFilter(pdfFilter);
			fc.setMultiSelectionEnabled(false);
			int returnVal = fc.showOpenDialog(this);
			if (returnVal == JFileChooser.APPROVE_OPTION) {
				try {
					prevDirChoice = fc.getSelectedFile();
					openFile(fc.getSelectedFile());
				} catch (IOException ioe) {
					ioe.printStackTrace();
				}
			}
		} catch (Exception e) {
			JOptionPane.showMessageDialog(split,
					"Opening files from your local " +
					"disk is not available\nfrom the " +
					"Java Web Start version of this " +
					"program.\n",
					"Error opening directory",
					JOptionPane.ERROR_MESSAGE);
			e.printStackTrace();
		}
	}
	*/

	/**
	 * Open URL ot a local file, given a string filename
	 * @param name the name of the file to open
	 */
	public void openFile(String name) {
		try {
			openFile(new URL(name));
		} catch (IOException ioe) {
			try {
				openFile(new File(name));
			} catch (IOException ex) {
				Logger.getLogger(PDFViewer.class.getName()).log(Level.SEVERE, null, ex);
			}
		}
	}

	/**
	 * Posts the Page Setup dialog
	 */
	//public void doPageSetup() {
	//	  PrinterJob printerJob = PrinterJob.getPrinterJob();
	//	  pageFormat = printerJob.pageDialog(getPageFormat());
	//}

	class PDFPrint implements Printable {

		/** The PDFFile to be printed */
		private PDFFile file;

		public PDFPrint(PDFFile file) {
			this.file = file;
		}

		public int print(Graphics g, PageFormat pageFormat, int index) throws PrinterException {

			//if (index > 0) return NO_SUCH_PAGE;

			int pagenum = index + 1;

			// don't bother if the page number is out of range.
			if ((pagenum >= 1) && (pagenum <= file.getNumPages())) {

				// fit the PDFPage into the printing area
				Graphics2D g2 = (Graphics2D) g;
				PDFPage page = file.getPage(pagenum);

				double pwidth  = pageFormat.getImageableWidth();
				double pheight = pageFormat.getImageableHeight();
				double paperaspect = pwidth / pheight;

				System.out.println("Paper size: " + pwidth + " x " + pheight);
				System.out.println("Paper aspect: " + paperaspect);

				double aspect = page.getAspectRatio();

				int width;
				int height;
				if (aspect > paperaspect) {
					// paper is too tall / pdfpage is too wide
					System.out.println("paper is too tall / pdfpage is too wide");
					height = (int) (pwidth / aspect);
					width = (int) pwidth;
				} else {
					// paper is too wide / pdfpage is too tall
					System.out.println("paper is too wide / pdfpage is too tall");
					width = (int) (pheight * aspect);
					height = (int) pheight;
				}

				System.out.println("Finally: " + width + " x " + height);

				Rectangle imgbounds = new Rectangle(
					(int) pageFormat.getImageableX(),
					(int) pageFormat.getImageableY(),
					width,
					height
				);

				// render the page
				PDFRenderer pgs = new PDFRenderer(page, g2, imgbounds, null, null);
				try {
					page.waitForFinish();
					pgs.run();
				} catch (InterruptedException ie) {
				}
				return PAGE_EXISTS;
			} else {
				return NO_SUCH_PAGE;
			}
		}
	}

	/**
	 * Print the current document.
	 */
	public void doPrint() {
		PrinterJob printerJob = PrinterJob.getPrinterJob();
		printerJob.setJobName(docName);

		if (pageFormat == null) {
			pageFormat = PrinterJob.getPrinterJob().defaultPage();
			System.out.println("+ Default imageable area: " + pageFormat.getImageableX() + ", " + pageFormat.getImageableY() + ", " + pageFormat.getImageableWidth() + ", " + pageFormat.getImageableHeight());
		}

		Book book = new Book();
		book.append(new PDFPrint(curFile), pageFormat, curFile.getNumPages());
		printerJob.setPageable(book);

		if (printerJob.printDialog()) {

			Paper paper = pageFormat.getPaper();

			// set printable area to maximum
			MediaSizeName msn = MediaSize.findMedia((float)paper.getWidth() / 72, (float)paper.getHeight() / 72, Size2DSyntax.INCH);
			System.out.println("+ Media size name: " + msn);
			if (msn != null) {
				PrintService ps = printerJob.getPrintService();
				PrintRequestAttributeSet aset = new HashPrintRequestAttributeSet();
				aset.add(MediaSizeName.ISO_A4);
				MediaPrintableArea[] mpas = (MediaPrintableArea[])ps.getSupportedAttributeValues(MediaPrintableArea.class, null, aset);
				if (mpas != null) {
					if (mpas.length == 1) {
						MediaPrintableArea mpa = mpas[0];
						float x = 72 * mpa.getX(MediaPrintableArea.INCH);
						float y = 72 * mpa.getY(MediaPrintableArea.INCH);
						float w = 72 * mpa.getWidth(MediaPrintableArea.INCH);
						float h = 72 * mpa.getHeight(MediaPrintableArea.INCH);

						System.out.println("+ Setting printable area: " + x + ", " + y + ", " + w + ", " + h);

						paper.setImageableArea(x,y,w,h);
						pageFormat.setPaper(paper);

						//pageFormat = printerJob.pageDialog(pageFormat);
					}
					else {
						System.out.println("* MediaPrintableArea query: expected single object, got " + mpas.length);
					}
				}

			}

			// setup orientation by first page
			pageFormat.setOrientation(curFile.getPage(1).getAspectRatio() > 1.0 ? PageFormat.LANDSCAPE : PageFormat.PORTRAIT);

			try {
				printerJob.print();
			} catch (PrinterException e) {
				JOptionPane.showMessageDialog(PDFViewer.this,
						"Printing Error: " + e.getMessage(),
						"Print Aborted",
						JOptionPane.ERROR_MESSAGE);
			}
		}
	}

	/**
	 * Close the current document.
	 */
	public void doClose() {
		if (thumbs != null) {
			thumbs.stop();
		}
		if (useThumbs) {
			thumbs = new ThumbPanel(null);
			thumbscroll.getViewport().setView(thumbs);
		}

		page.showPage(null);
		curFile = null;
		setEnabling();
	}


	public void doZoom(float factor) {
		page.setPreferredSize(new Dimension(
			Math.max(MIN_ZOOM_SIZE, Math.min(MAX_ZOOM_SIZE, Math.round(page.getPreferredSize().width * factor))),
			Math.max(MIN_ZOOM_SIZE, Math.min(MAX_ZOOM_SIZE, Math.round(page.getPreferredSize().height * factor)))
		));
		page.revalidate();
	}

	/**
	 * makes the page fit in the window
	 */
	public void doFit(boolean width, boolean height) {
		assert width || height;

		Dimension viewSize = scrollPage.getViewport().getSize();

		// calculate viewSize without scrollbars
		if (scrollPage.getHorizontalScrollBar().isVisible()) {
			viewSize.height += scrollPage.getHorizontalScrollBar().getHeight();
		}
		if (scrollPage.getVerticalScrollBar().isVisible()) {
			viewSize.width += scrollPage.getVerticalScrollBar().getWidth();
		}

		Dimension imageSize = page.getPage().getUnstretchedSize(width ? viewSize.width : 1000000, height ? viewSize.height : 1000000, null);
		Dimension realImageSize = (Dimension)imageSize.clone();

		// avoid horizontal scrollbar if vertical scrollbar expected
		// and vice versa
		if (imageSize.width > viewSize.width) {
			realImageSize.height -= scrollPage.getHorizontalScrollBar().getHeight();
		}
		if (imageSize.height > viewSize.height) {
			realImageSize.width -= scrollPage.getVerticalScrollBar().getWidth();
		}

		page.setPreferredSize(realImageSize);
		page.revalidate();
	}

	/**
	 * Shows or hides the thumbnails by moving the split pane divider
	 */
	public void doThumbs(boolean show) {
		if (show) {
			split.setDividerLocation((int) thumbs.getPreferredSize().width +
					(int) thumbscroll.getVerticalScrollBar().
					getWidth() + 4);
		} else {
			split.setDividerLocation(0);
		}
	}

	/**
	 * Handle a key press for navigation
	 */
	public void keyPressed(KeyEvent evt) {
		int code = evt.getKeyCode();
		switch (evt.getKeyCode()) {
			//case KeyEvent.VK_LEFT:
			//case KeyEvent.VK_UP:
			case KeyEvent.VK_PAGE_UP:
				incPage(-1);
				return;
			//case KeyEvent.VK_RIGHT:
			//case KeyEvent.VK_DOWN:
			case KeyEvent.VK_PAGE_DOWN:
				incPage(+1);
				return;
			case KeyEvent.VK_HOME:
				gotoPage(0);
				return;
			case KeyEvent.VK_END:
				gotoPage(-1);
				return;
		}
		switch (evt.getKeyChar()) {
			case '+':
				doZoom(ZOOM_FACTOR);
				return;
			case '-':
				doZoom(1f/ZOOM_FACTOR);
				return;
		}
	}

	///////////////////////////////////////////////////////////////////////////
	// page builder

	/**
	 * Combines numeric key presses to build a multi-digit page number.
	 */
	class PageBuilder implements Runnable {

		int value = 0;
		long timeout;
		Thread anim;
		static final long TIMEOUT = 500;

		/** add the digit to the page number and start the timeout thread */
		public synchronized void keyTyped(int keyval) {
			value = value * 10 + keyval;
			timeout = System.currentTimeMillis() + TIMEOUT;
			if (anim == null) {
				anim = new Thread(this);
				anim.setName(getClass().getName());
				anim.start();
			}
		}

		/**
		 * waits for the timeout, and if time expires, go to the specified
		 * page number
		 */
		public void run() {
			long now, then;
			synchronized (this) {
				now = System.currentTimeMillis();
				then = timeout;
			}
			while (now < then) {
				try {
					Thread.sleep(timeout - now);
				} catch (InterruptedException ie) {
				}
				synchronized (this) {
					now = System.currentTimeMillis();
					then = timeout;
				}
			}
			synchronized (this) {
				gotoPage(value - 1);
				anim = null;
				value = 0;
			}
		}
	}
	PageBuilder pb = new PageBuilder();

	public void keyReleased(KeyEvent evt) {
	}

	/**
	 * gets key presses and tries to build a page if they're numeric
	 */
	public void keyTyped(KeyEvent evt) {
		char key = evt.getKeyChar();
		if (key >= '0' && key <= '9') {
			int val = key - '0';
			pb.keyTyped(val);
		}
	}

	///////////////////////////////////////////////////////////////////////////
	// TEST

	public static void main(String args[]) {

		// start the viewer
		final PDFViewer viewer;
		viewer = new PDFViewer(false);
		viewer.openFile(args[0]);

		final JFrame frame = new JFrame("SwingLabs PDF Viewer");
		frame.add(viewer);
		frame.pack();
		frame.setVisible(true);

		frame.addWindowListener(new WindowAdapter() {
			public void windowClosing(WindowEvent evt) {
				viewer.doClose();
				frame.dispose();
				System.exit(0);
			}
		});

	}
}
