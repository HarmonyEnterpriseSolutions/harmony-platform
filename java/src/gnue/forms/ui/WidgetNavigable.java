package gnue.forms.ui;
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import gnue.forms.rpc.RpcException;

/*
 * Widget
 *	   can have focus
 *	   reports if focus gained (calls onSetFocus)
 *
 *
 */

public class WidgetNavigable extends Widget {

	static Object lastFocusOwner = null;

	public WidgetNavigable(Desktop desktop, Integer id) {
		super(desktop, id);
	}

	public WidgetNavigable(Desktop desktop, Integer id, String label) {
		super(desktop, id, label);
	}

	public WidgetNavigable(Desktop desktop, Integer id, String label, String tip) {
		super(desktop, id, label, tip);
	}

	/** overrideable, returns component that accepts focus */
	public JComponent getFocusComponent() {
		return getComponent();
	}

	public void uiSetFocus() {
		getFocusComponent().requestFocus();
		// remember last widget focus requested on to suppres consequent onSetFocus in this case
		// because logical focus already on this widget
		getDesktop().lastRequestFocusWidgetId = getId();
	}

	protected void setComponent(JComponent component) {
		super.setComponent(component);
		getFocusComponent().addFocusListener(new FocusAdapter() {
			public void focusGained(FocusEvent event) {
				// avoid onSetFocus if focus was requested
				if (getId().equals(getDesktop().lastRequestFocusWidgetId)) {
					getDesktop().lastRequestFocusWidgetId = null;
				}
				else {
					// avoid subsequent onSetFocus when browser window activated
					if (event.getSource() != lastFocusOwner) {
						callAfter("onSetFocus");
						lastFocusOwner = event.getSource();
					}
				}
			}
		});

		// disable focus traversal
		getFocusComponent().setFocusTraversalKeysEnabled(false);

		// use server focus management
		getFocusComponent().addKeyListener(new KeyAdapter() {
			public void keyPressed(final KeyEvent event) {
				SwingUtilities.invokeLater(new Runnable(){
					public void run() {
						onKeyPressed(event);
						flushIfPending();
					}
				});
			}
		});
	}

	//-------------------------------------------------------------------------
	// KeyEvent
	//
	protected boolean isNavigationEvent(KeyEvent event) {
		switch (event.getKeyCode()) {
			case KeyEvent.VK_TAB:
			case KeyEvent.VK_ESCAPE:
				return true;
			default:
				return false;
		}
	}

	/**
	 * invoked by WidgetNavigable.keyListener
	 * registered to component in WidgetNavigable.setComponent
	 * use appendCall instead call (appended calls will be flushed)
	 */
	protected boolean onKeyPressed(KeyEvent event) {
		boolean navigation = isNavigationEvent(event);
		if (navigation) {
			//ystem.out.println("KEY PRESSED: " + event.getKeyCode());
			appendCall("onKeyPressed", event.getKeyCode(), event.isShiftDown(), event.isControlDown(), event.isAltDown());
		}
		return navigation;
	}

}
