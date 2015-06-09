package gnue.forms.ui;
import gnue.forms.rpc.*;
import javax.swing.*;
import java.awt.*;
import java.net.*;
import java.io.*;
import java.util.*;
import gnue.forms.components.Utils;
import gnue.forms.components.MessageDetailsDialog;
import gnue.forms.components.DesktopComponent;
import gnue.forms.components.PaneDesktopComponent;
import gnue.forms.components.RegularDesktopComponent;
import gnue.forms.components.FrameComponent;

import javax.swing.event.InternalFrameEvent;

public class Desktop extends RemoteHive {

	protected ClientContext clientContext;

	protected DesktopComponent desktopComponent;
	protected String staticResourceService;
	protected String dynamicResourceService;
	private Map<String, Icon>icons = new HashMap<String, Icon>();
	RootPaneContainer parent;
	
	// used only by WidgetNavigable		
	Integer lastRequestFocusWidgetId = null;
	
	public Desktop(RootPaneContainer parent, ClientContext clientContext, JSONHttpService service, String staticResourceService, String dynamicResourceService, boolean standalone, boolean debug) {
		super(new String[]{"gnue.forms.ui"}, service, debug);
		this.parent = parent;
		this.clientContext = clientContext;
		this.staticResourceService = staticResourceService;
		this.dynamicResourceService = dynamicResourceService;

		this.desktopComponent = standalone ? new RegularDesktopComponent() : new PaneDesktopComponent();
	}


	InputStream openStaticResource(String key) throws IOException {
		try {
			return new BufferedInputStream(new URL(staticResourceService + key).openStream());
		}
		catch (MalformedURLException e) {
			throw new RuntimeException("MalformedURLException");
		}
	}

	public URL wrapUrl(String url) {
		try {
			return new URL(dynamicResourceService + "?URL=" + URLEncoder.encode(url, "UTF-8"));
		}
		catch (MalformedURLException e) {
			throw new RuntimeException("MalformedURLException");
		}
		catch (UnsupportedEncodingException e) {
			throw new RuntimeException("UnsupportedEncodingException");
		}
	}

	Icon getStaticResourceIcon(String key)  {
		Icon icon = icons.get(key);
		if (icon == null) {
			try {
				icons.put(key, icon = new ImageIcon(new URL(staticResourceService.toString() + key)));
			}
			catch (MalformedURLException e) {
				throw new RuntimeException("MalformedURLException");
			}
		}
		return icon;
	}

	/**
	 * may return null if pane not asociated with swing Component
	 */
	public Component getComponent() {
		return desktopComponent.asComponent();
	}

	DesktopComponent getDesktopComponent() {
		return desktopComponent;
	}

	public ClientContext getClientContext() {
		return clientContext;
	}

	public Object flush() throws RpcException {
		beginWait();
		try {
			try {
				return super.flush();
			}
			catch (ServerSideRpcException e) {
				String prefix = "SessionNotFoundError: ";
				if (("" + e.getMessage()).startsWith(prefix)) {
					JOptionPane.showMessageDialog(
						this.desktopComponent.asComponent(), 
						e.getMessage().substring(prefix.length()),
						"Session not found",
						JOptionPane.ERROR_MESSAGE
					);
					reset();
					return super.flush();
				}
				else {
					throw e;
				}
			}
		}
		finally {
			endWait();
		}
	}
	
	public void closeAll() {
		// sending close event to all frames on desktop, called on applet stop
		// this has no effect because frames will not receive events (because after applet stop?)
		beginWait();
		try {
			for (FrameComponent f: desktopComponent.getAllFrameComponents()) {
				f.postCloseEvent();
			}
		}
		finally {
			endWait();
		}
	}

	public void printStackTrace(Throwable e, String category) {
		super.printStackTrace(e);
		final StringWriter w = new StringWriter();
		e.printStackTrace(new PrintWriter(w));
		new MessageDetailsDialog(desktopComponent.asComponent(), category, category, w.toString(), JOptionPane.ERROR_MESSAGE, true);
	}

	private Stack<Cursor> cursors = new Stack<Cursor>();
	//private Stack<HourglassCursorThread> cursors = new Stack<HourglassCursorThread>();

	public void beginWait() {
		Component glass = parent.getGlassPane();
		glass.setVisible(true);
		cursors.push(glass.getCursor());
		glass.setCursor(Cursor.getPredefinedCursor(Cursor.WAIT_CURSOR));
		//HourglassCursorThread t = new HourglassCursorThread(getCursorComponent());
		//cursors.push(t);
		//t.start();
	}

	public void endWait() {
		try {
			Component glass = parent.getGlassPane();
			glass.setCursor(cursors.pop());
			glass.setVisible(false);
			//cursors.pop().restoreCursor();
		}
		catch (EmptyStackException e) {
			System.err.println("! Desktop: endWait without beginWait");
			e.printStackTrace();
		}
	}

	public void reset() {
		super.reset();
		// dispose opened dialogs
		for (Window w: Window.getWindows()) {
			if (w instanceof JDialog) {
				w.dispose();
			}
		}
		for (FrameComponent frame: desktopComponent.getAllFrameComponents()) {
			frame.dispose();
		}
	}
	
	/*
	//Attempt to supress "short term" hourglass cursor

	public class HourglassCursorThread extends Thread {
		Component component;
		Cursor oldCursor;

		public HourglassCursorThread(Component c) {
			component = c;
			oldCursor = c.getCursor();
		}

		public void run() {
		 	try {
		 		sleep(1);
				component.setCursor(Cursor.getPredefinedCursor(Cursor.WAIT_CURSOR));
		 	}
		 	catch (InterruptedException e) {
		 	}
		}

		public void restoreCursor() {
			interrupt();
			component.setCursor(oldCursor);
		}
	}
	*/

	Queue<RemoteCall> laterCalls = new LaterCalls();

	/**
	 * queue call and invoke all queued calls later
	 */
	public void callAfter(RemoteCall call) {
		laterCalls.offer(call);
	}

	class LaterCalls extends LinkedList<RemoteCall> implements Runnable {

		public LaterCalls() {
		}

		public boolean offer(RemoteCall call) {
			if (debug) System.out.println("Calling after " + call);
			SwingUtilities.invokeLater(this);
			return super.offer(call);
		}

		/**
		 * perform all queued calls
		 */
		public void run() {
			try {
				RemoteCall call = poll();
				if (call != null) {
					if (debug) System.out.println("---------- later calls ----------");
				}
				while (call != null) {
					if (debug) System.out.println("Later call " + call);
					call.append();
					call = poll();
				}
				if (isPending()) {
					flush();
				}
			}
			catch (RpcException e) {
				printStackTrace(e, "Remote error");
			}
		}

	}


}
