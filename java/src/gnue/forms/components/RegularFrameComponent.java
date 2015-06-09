package gnue.forms.components;

import javax.swing.JFrame;
import javax.swing.JComponent;
import javax.swing.JPanel;
import java.awt.event.WindowEvent;
import java.awt.Toolkit;
import java.awt.Rectangle;
import java.awt.Dimension;
import java.awt.BorderLayout;
import java.awt.Frame;

public class RegularFrameComponent extends JFrame implements FrameComponent {
	
	RegularFrameComponent(String title, boolean resizable, boolean closable, boolean maximizable, boolean iconifiable) {
		super(title);
		setResizable(resizable);
		// closable, maximizable, iconifiable ignored, allways true?
		setContentPane(new JPanel(new BorderLayout()));
	}
	
	public void postCloseEvent() {
		Toolkit.getDefaultToolkit().getSystemEventQueue().postEvent(new WindowEvent(this, WindowEvent.WINDOW_CLOSING));
	}
	
	public JComponent asComponent() {
		return (JComponent)getContentPane();
	}

	public void show(boolean modal, boolean maximize, boolean fit, Rectangle bounds) {
		// do not setVisible, just set bounds
		if (fit) {
			pack();
			centerOnScreen();
		}
		else if (bounds != null) {
			// set delayed state bounds
			setBounds(bounds);
		}
		else if (getBounds().isEmpty()) {
			// set default size based on screen size
			Dimension psize = Toolkit.getDefaultToolkit().getScreenSize();
			setSize(psize.width-40, psize.height-80);
			centerOnScreen();
		}
		if (maximize) {
			setExtendedState(getExtendedState()|JFrame.MAXIMIZED_BOTH);
		}
	}
	
	public void doHide() {
		setVisible(false);
	}
		
	public void dispose() {
		super.dispose();
		// later exit if nothing visible
		javax.swing.SwingUtilities.invokeLater(new Runnable() {
			public void run() {
				boolean exit = true;
				for (Frame f: Frame.getFrames()) {
					if (f.isVisible()) {
						exit = false;
					}
				}
				if (exit) {
					System.exit(0);
				}
			}
		});
	}

	protected void centerOnScreen() {
		// center on parent
		Dimension size = getSize();
		Dimension psize = Toolkit.getDefaultToolkit().getScreenSize();
		
		// resize to fit screen
		size.width  = Math.min(size.width,  psize.width);
		size.height = Math.min(size.height, psize.height);
		
		setBounds((psize.width - size.width) / 2, (psize.height - size.height) / 2, size.width, size.height);
	}

}
