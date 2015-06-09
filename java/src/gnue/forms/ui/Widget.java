package gnue.forms.ui;

import gnue.forms.rpc.*;
import gnue.forms.ui.Desktop;
import java.awt.*;
import javax.swing.*;
import org.json.*;
import java.util.*;

/**
 * Any widget
 *	   has JComponent
 *	   may have JLabel
 *	   may have tip
 *     may save state
 */
public class Widget extends RemoteObject {

	private JLabel label = null;
	private JComponent component;
	private String tip = "";
	private boolean visible = true;
	private boolean horizontalGrowable = true;
	private int anchor = GridBagConstraints.WEST;

	public Widget(Desktop desktop, Integer id) {
		super(desktop, id);

		// appears only as Widget in method parameters
		hive.addClassTranslation(getClass(), Widget.class);
	}

	public Widget(Desktop desktop, Integer id, String label) {
		this(desktop, id);
		if (label != null && label.length() > 0) {
			this.label = new JLabel(label);
			if (Box.DEBUG) {
				this.label.setBorder(BorderFactory.createEtchedBorder());
			}
		}
	}

	public Widget(Desktop desktop, Integer id, String label, String tip) {
		this(desktop, id, label);
		this.tip = tip;
	}

	public final JComponent getComponent() {
		return component;
	}

	protected void setComponent(JComponent component) {
		this.component = component;
		if (tip.length() > 0) {
			component.setToolTipText(tip);
		}
	}

	public Desktop getDesktop() {
		return (Desktop) hive;
	}

	public void uiEnable(Boolean enable) {
		getComponent().setEnabled(enable);
	}

	public void uiSetVisible(Boolean visible) {
		getComponent().setVisible(visible);
	}

	public JLabel getLabel() {
		return label;
	}

	/**
	 * queue call and invoke all queued calls later
	 */
	public void callAfter(final String method, final Object... args) {
		getDesktop().callAfter(createCall(method, args));
	}

	public boolean isVerticalGrowable() {
		return false;
	}
	
	public boolean isHorizontalGrowable() {
		return horizontalGrowable;
	}

	public void uiSetHorizontalGrowable(Boolean horizontalGrowable) {
		this.horizontalGrowable = horizontalGrowable;
	}
	
	public void uiSetAnchor(Integer anchor) {
		switch(anchor) {
			case 1: this.anchor = GridBagConstraints.SOUTHWEST; break;
			case 2: this.anchor = GridBagConstraints.SOUTH;     break;
			case 3: this.anchor = GridBagConstraints.SOUTHEAST; break;
			case 4: this.anchor = GridBagConstraints.WEST;      break;
			case 5: this.anchor = GridBagConstraints.CENTER;    break;
			case 6: this.anchor = GridBagConstraints.EAST;      break;
			case 7: this.anchor = GridBagConstraints.NORTHWEST; break;
			case 8: this.anchor = GridBagConstraints.NORTH;     break;
			case 9: this.anchor = GridBagConstraints.NORTHEAST; break;
			default: throw new RuntimeException("Invalid anchor: " + anchor);
		}
	}
	
	public int getAnchor() {
		return anchor;
	}
	
	public int getFill() {
		boolean horizontalGrowable = this.isHorizontalGrowable();
		return this.isVerticalGrowable() 
			? (horizontalGrowable ? GridBagConstraints.BOTH       : GridBagConstraints.VERTICAL) 
			: (horizontalGrowable ? GridBagConstraints.HORIZONTAL : GridBagConstraints.NONE    );
	}

	public String getTip() {
		return tip;
	}


	//////////////////////////////////////////////////////////////////////////
	// state
	//
	public final void uiSetState(JSONObject state) {
		setState(state);
	}

	public final void uiGetState() {
		JSONObject state = getState();
		if (state != null) {
			callAfter("onGetState", state);
		}
	}

	public JSONObject getState() {
		return null;
	}

	public void setState(JSONObject state) {
	}

}
