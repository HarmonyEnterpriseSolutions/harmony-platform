/*
 * DesktopPane.java
 */

package gnue.forms;

import gnue.forms.ui.ClientContext;
import gnue.forms.ui.Desktop;
import gnue.forms.rpc.JSONHttpService;
import gnue.forms.rpc.MemoryCookieStore;
import gnue.forms.rpc.RpcCookiePolicy;
import gnue.forms.rpc.SSLUtilities;

import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import java.util.*;
import java.net.*;

/**
 *
 * @author  Oleg Noga
 * @version $Revision: 1.30 $
 */
public class Applet extends JApplet implements ClientContext, Runnable {

	Desktop desktop;

	final protected static float METAL_FONT_SIZE_CHANGE = -1f;
	protected static Map uiConfig = new HashMap();
	protected static LookAndFeel lookAndFeel;
	protected boolean standalone = false;
		
	static {
    	// this fixes d3d relative repaint bug introduced in java 1.6 u10
    	System.setProperty("sun.java2d.d3d", "false");

		// set windows LF if suggested		
		String lfClassName = UIManager.getSystemLookAndFeelClassName();
		if (!lfClassName.equals("com.sun.java.swing.plaf.windows.WindowsLookAndFeel")) {
			// stay on metal if not windows, because closable tabbed pane supports only metal and windows
			lfClassName = "javax.swing.plaf.metal.MetalLookAndFeel";
		}
		
		try { 
			UIManager.setLookAndFeel(lfClassName);	
		} 
		catch (Exception e) {
			e.printStackTrace(); 
		}
		
		Applet.lookAndFeel = UIManager.getLookAndFeel();
			
		UIDefaults defaults = UIManager.getDefaults();

		/*for (Enumeration keys = defaults.keys(); keys.hasMoreElements(); ) {
			Object key = keys.nextElement();
			Font font = defaults.getFont(key);
			if (font != null) {
				System.out.println(key + ": " + font);
			}
		}*/

		if ("Metal".equals(UIManager.getLookAndFeel().getID())) {
			// set all fonts smaller and plain
			for (Enumeration keys = defaults.keys(); keys.hasMoreElements(); ) {
				Object key = keys.nextElement();
				Font font = defaults.getFont(key);
				if (font != null) {
					//System.out.println(key + ": " + font);
					uiConfig.put(key, font.deriveFont(Font.PLAIN, font.getSize2D() + METAL_FONT_SIZE_CHANGE));
				}
			}
			uiConfig.put("Desktop.background", new Color(153, 153, 204));
		}

		else if ("Windows".equals(UIManager.getLookAndFeel().getID())) {
			// JTextArea has monospaced font 9px, this is too small, make same as JTextField font
			Font font = UIManager.getFont("TextField.font");
			if (font != null) {
				uiConfig.put("TextArea.font", font);
			}
		}

	}

	public void init() {
		
		try { 
			UIManager.setLookAndFeel(Applet.lookAndFeel);
		} 
		catch (Exception e) {
			e.printStackTrace(); 
		}
				
		// under MSIE, all UIManager settings made in static lost after page refresh
		// therefore making UIManager setup here, after page refresh
		for (Object key: uiConfig.keySet()) {
			UIManager.put(key, uiConfig.get(key));
		}
		
		try {
			//ystem.out.println(getCodeBase());
			// http://localhost/harmony/wk.cgi/harmony/
			boolean debug = getParameter("debug") != null && !getParameter("debug").equals("0");
			
			URL jsonServiceUrl = getCodeBase();
			
			if (!jsonServiceUrl.toString().endsWith("/javaui/")) {
				// old webkit service
				jsonServiceUrl = new URL(jsonServiceUrl.toString() + "javaui");
			}
			
			desktop = new Desktop(
				this,
				this,
				new JSONHttpService(jsonServiceUrl, debug),
				getCodeBase() + "staticres/",
				getCodeBase() + "dynamicres/",
				standalone,
				debug
			);
			
			if (desktop.getComponent() != null) {
				add(desktop.getComponent());
			}
			//ystem.out.println(gnue.forms.components.Utils.getTopLevelFrame(Applet.this).isVisible());
			//gnue.forms.components.Utils.getTopLevelFrame(Applet.this).setVisible(true);
			//ystem.out.println(gnue.forms.components.Utils.getTopLevelFrame(Applet.this).isVisible());
		}
		catch(Exception e) {
			e.printStackTrace(System.out);
		}
	}

	public void run() {
		try {
			desktop.flush();
		}
		catch(Exception e) {
			e.printStackTrace(System.out);
		}
	}

	public void start() {
		if (SwingUtilities.isEventDispatchThread()) {
			run();
		}
		else {
			//ystem.out.println("* Applet.start: not an event dispatch thread");
			SwingUtilities.invokeLater(this);
		}
	}

	public void stop() {
		Runnable stop = new Runnable() {
			public void run() {
				desktop.closeAll();
			}
		};
		if (SwingUtilities.isEventDispatchThread()) {
			stop.run();
		}
		else {
			//ystem.out.println("* Applet.start: not an event dispatch thread");
			SwingUtilities.invokeLater(stop);
		}
	}

	public void saveDocument(URL url) {
		getAppletContext().showDocument(url, "_blank");
	}
	
	static public JApplet createInFrame(JFrame frame) {
		Applet applet = new Applet();
		//applet.setFrame(frame);
		//applet.userCreated = true;
		frame.setContentPane(applet.getContentPane());
		applet.init();
		return applet;
	}
	
	
	/*
	 * if standalone, get parameter from other place
	 */
	public String getParameter(String name) {
		if (standalone) {
			return System.getProperty("gnue.forms." + name);
		}
		else {
			return super.getParameter(name);
		}
	}
	
	public URL getCodeBase() {
		if (standalone) {
			try {
				String codebase = System.getProperty("gnue.forms.codebase");
				if (codebase == null) {
					codebase = ResourceBundle.getBundle("javaui").getString("codebase");
					System.out.println("* Property gnue.forms.codebase is null, getting codebase from resources: " + codebase);
				}
				return new URL(codebase);
			}
			catch (MalformedURLException e) {
				throw new RuntimeException(e);
			}
		}
		else {
			return super.getCodeBase();
		}
	}
	
	/**
	 * Accepted args are codebase=<...> [debug=<0|1>]
	 */
	public static void main(String args[]) {

		for (String arg: args) {
			String[] k_v = arg.split("=", 2);
			if (k_v.length == 2) {
				System.setProperty("gnue.forms." + k_v[0].trim(), k_v[1].trim());
			}
			else {
				System.err.println("* command line arg ignored: '" + arg + "'");
			}
		}
		
		/*JFrame frame = new JFrame("GNUe forms java client web start");
		
		Dimension screenSize = Toolkit.getDefaultToolkit().getScreenSize();
		frame.setSize(screenSize.width - 40, screenSize.height - 80);
		frame.setLocation((screenSize.width - frame.getSize().width) / 2, (screenSize.height - frame.getSize().height) / 2) ;
		*/

		// setup memory cookie jar to hold session
	    //CookieStore store = new MemoryCookieStore();
	    //CookiePolicy policy = new RpcCookiePolicy();
	    //CookieManager handler = new CookieManager(store, policy);
	    //CookieHandler.setDefault(handler);
	    
	    if (CookieHandler.getDefault() == null) {
			// not under Java Web Start
			// set our own cookie handler
			CookieManager customCookieManager = new CookieManager(); 
			customCookieManager.setCookiePolicy(CookiePolicy.ACCEPT_ALL); 
			CookieHandler.setDefault(customCookieManager);
	    	
			// Install the all-trusting host name verifier
			// http://en.wikibooks.org/wiki/WebObjects/Web_Services/How_to_Trust_Any_SSL_Certificate
			SSLUtilities.trustAllHostnames();
			SSLUtilities.trustAllHttpsCertificates();
	    }
	    
		final Applet applet = new Applet();
		applet.standalone = true;
		//frame.setContentPane(applet.getContentPane());

		applet.init();
		applet.start();
		
		/*frame.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
		frame.addWindowListener(new WindowAdapter() {
			public void windowClosed(WindowEvent e) {
				applet.stop();
				applet.destroy();
				System.exit(0);
			}
		});
		
  		frame.setVisible(true);*/
	}
}
